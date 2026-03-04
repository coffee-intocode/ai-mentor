"""AI chat service with persistence orchestration."""

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic_ai.messages import (
    BuiltinToolCallPart,
    BuiltinToolReturnPart,
    FilePart,
    ModelRequest,
    ModelResponse,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.run import AgentRunResult
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Conversation, Message
from ..repositories import ConversationRepository, MessageRepository


@dataclass(slots=True)
class PreparedChatRun:
    """Prepared chat run metadata used during stream finalization."""

    conversation_id: int
    owner_id: int
    assistant_client_message_id: str
    superseded_target_message_id: int | None


def to_json_safe(value: Any) -> Any:
    """Convert arbitrary values into JSON-serializable structures."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        try:
            return json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return repr(value)


def serialize_ui_parts(message: UIMessage) -> list[dict[str, Any]]:
    """Serialize UI message parts for durable storage."""
    return [to_json_safe(part.model_dump(by_alias=True, exclude_none=True)) for part in message.parts]


def extract_text_from_ui_message(message: UIMessage) -> str:
    """Extract full textual content from a UI message."""
    text_parts = [part.text for part in message.parts if isinstance(part, TextUIPart)]
    return '\n'.join(part for part in text_parts if part).strip()


def find_latest_user_message(messages: list[UIMessage]) -> UIMessage | None:
    """Find the latest user message from a Vercel AI message list."""
    for message in reversed(messages):
        if message.role == 'user':
            return message
    return None


def serialize_assistant_response(
    result: AgentRunResult[Any],
) -> tuple[list[dict[str, Any]], str]:
    """Serialize assistant response parts and extract full assistant text."""
    stored_parts: list[dict[str, Any]] = []
    content_parts: list[str] = []
    tool_part_indexes: dict[str, int] = {}

    messages = result.new_messages()
    if not messages:
        messages = [result.response]

    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if not isinstance(part, ToolReturnPart):
                    continue

                tool_output = to_json_safe(part.content)
                tool_part = {
                    'type': f'tool-{part.tool_name}',
                    'toolCallId': part.tool_call_id,
                    'state': 'output-available',
                    'output': tool_output,
                    'providerExecuted': False,
                }
                tool_index = tool_part_indexes.get(part.tool_call_id)
                if tool_index is not None:
                    existing_tool_part = stored_parts[tool_index]
                    existing_tool_part['state'] = 'output-available'
                    existing_tool_part['output'] = tool_output
                else:
                    stored_parts.append(tool_part)
            continue

        if not isinstance(message, ModelResponse):
            continue

        for part in message.parts:
            if isinstance(part, TextPart):
                stored_parts.append({'type': 'text', 'text': part.content})
                if part.content:
                    content_parts.append(part.content)
                continue

            if isinstance(part, ThinkingPart):
                stored_parts.append({'type': 'reasoning', 'text': part.content})
                continue

            if isinstance(part, BuiltinToolCallPart):
                tool_part_indexes[part.tool_call_id] = len(stored_parts)
                stored_parts.append(
                    {
                        'type': f'tool-{part.tool_name}',
                        'toolCallId': part.tool_call_id,
                        'state': 'input-available',
                        'input': part.args_as_dict(),
                        'providerExecuted': True,
                    }
                )
                continue

            if isinstance(part, ToolCallPart):
                tool_part_indexes[part.tool_call_id] = len(stored_parts)
                stored_parts.append(
                    {
                        'type': f'tool-{part.tool_name}',
                        'toolCallId': part.tool_call_id,
                        'state': 'input-available',
                        'input': part.args_as_dict(),
                        'providerExecuted': False,
                    }
                )
                continue

            if isinstance(part, BuiltinToolReturnPart):
                tool_output = to_json_safe(part.content)
                tool_part = {
                    'type': f'tool-{part.tool_name}',
                    'toolCallId': part.tool_call_id,
                    'state': 'output-available',
                    'output': tool_output,
                    'providerExecuted': True,
                }
                tool_index = tool_part_indexes.get(part.tool_call_id)
                if tool_index is not None:
                    existing_tool_part = stored_parts[tool_index]
                    existing_tool_part['state'] = 'output-available'
                    existing_tool_part['output'] = tool_output
                else:
                    stored_parts.append(tool_part)
                continue

            if isinstance(part, FilePart):
                stored_parts.append(
                    {
                        'type': 'file',
                        'mediaType': part.content.media_type,
                        'url': part.content.data_uri,
                    }
                )
                continue

            stored_parts.append({'type': type(part).__name__, 'repr': repr(part)})

    full_text = '\n'.join(part for part in content_parts if part).strip()
    return [to_json_safe(part) for part in stored_parts], full_text


class AiChatService:
    """Business logic service for AI chat persistence flows."""

    def __init__(
        self,
        db: AsyncSession,
        conversation_repository: ConversationRepository | None = None,
        message_repository: MessageRepository | None = None,
    ):
        self.db = db
        self.conversation_repository = conversation_repository or ConversationRepository(db)
        self.message_repository = message_repository or MessageRepository(db)

    async def _get_authorized_conversation(self, conversation_id: int, owner_id: int) -> Conversation:
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation or conversation.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Conversation not found',
            )
        return conversation

    async def prepare_chat_run(
        self,
        *,
        run_input: Any,
        conversation_id: int,
        owner_id: int,
    ) -> PreparedChatRun:
        """Validate request trigger and persist pre-stream data."""
        conversation = await self._get_authorized_conversation(conversation_id, owner_id)
        superseded_target: Message | None = None
        trigger = getattr(run_input, 'trigger', None)

        if trigger == 'submit-message':
            user_message = find_latest_user_message(run_input.messages)
            if user_message is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='User message not found in request',
                )

            existing_user_message = await self.message_repository.get_by_client_message_id(
                conversation_id=conversation.id,
                owner_id=owner_id,
                client_message_id=user_message.id,
            )

            if existing_user_message is None:
                user_parts = serialize_ui_parts(user_message)
                user_text = extract_text_from_ui_message(user_message)
                if not user_text:
                    user_text = json.dumps(user_parts, ensure_ascii=True)

                await self.message_repository.create(
                    Message(
                        conversation_id=conversation.id,
                        owner_id=owner_id,
                        role='user',
                        content=user_text,
                        parts_json=user_parts,
                        client_message_id=user_message.id,
                    )
                )
        elif trigger == 'regenerate-message':
            target_message_id = getattr(run_input, 'message_id', None)
            if not target_message_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='message_id is required for regeneration',
                )

            superseded_target = await self.message_repository.get_by_client_message_id(
                conversation_id=conversation.id,
                owner_id=owner_id,
                client_message_id=target_message_id,
            )
            if superseded_target is None or superseded_target.role != 'assistant':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Assistant message not found for regeneration',
                )
        else:  # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported trigger '{trigger}'",
            )

        return PreparedChatRun(
            conversation_id=conversation.id,
            owner_id=owner_id,
            assistant_client_message_id=str(uuid4()),
            superseded_target_message_id=superseded_target.id if superseded_target is not None else None,
        )

    async def persist_assistant_completion(
        self,
        *,
        prepared_run: PreparedChatRun,
        result: AgentRunResult[Any],
    ) -> Message:
        """Persist assistant response and apply regenerate supersede linkage."""
        assistant_parts, assistant_text = serialize_assistant_response(result)
        if not assistant_text:
            assistant_text = json.dumps(assistant_parts, ensure_ascii=True)

        assistant_message = await self.message_repository.create(
            Message(
                conversation_id=prepared_run.conversation_id,
                owner_id=prepared_run.owner_id,
                role='assistant',
                content=assistant_text,
                parts_json=assistant_parts,
                client_message_id=prepared_run.assistant_client_message_id,
            )
        )

        if prepared_run.superseded_target_message_id is not None:
            superseded_target = await self.message_repository.get_by_id(prepared_run.superseded_target_message_id)
            if superseded_target is not None:
                superseded_target.superseded_by_message_id = assistant_message.id

        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == prepared_run.conversation_id)
            .values(updated_at=func.now())
        )
        return assistant_message
