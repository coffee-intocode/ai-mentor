"""AI chat router with pydantic-ai integration."""

import json
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from pydantic_ai.builtin_tools import (
    AbstractBuiltinTool,
    CodeExecutionTool,
    ImageGenerationTool,
    WebSearchTool,
)
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
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent import agent
from ..dependencies import CurrentUser, get_db
from ..models import Conversation, Message
from ..repositories import ConversationRepository, MessageRepository

router = APIRouter(prefix="/chat", tags=["chat"])


# AI Model and Tool Type Definitions
AIModelID = Literal[
    "anthropic:claude-sonnet-4-5",
    "openai-responses:gpt-5",
    "google-gla:gemini-2.5-pro",
]
BuiltinToolID = Literal["web_search", "image_generation", "code_execution"]


class AIModel(BaseModel):
    """AI model configuration."""

    id: AIModelID
    name: str
    builtin_tools: list[BuiltinToolID]


class BuiltinTool(BaseModel):
    """Built-in tool definition."""

    id: BuiltinToolID
    name: str


# Available tools
BUILTIN_TOOL_DEFS: list[BuiltinTool] = [
    BuiltinTool(id="web_search", name="Web Search"),
    BuiltinTool(id="code_execution", name="Code Execution"),
    BuiltinTool(id="image_generation", name="Image Generation"),
]

BUILTIN_TOOLS: dict[BuiltinToolID, AbstractBuiltinTool] = {
    "web_search": WebSearchTool(),
    "code_execution": CodeExecutionTool(),
    "image_generation": ImageGenerationTool(),
}

# Available AI models
AI_MODELS: list[AIModel] = [
    AIModel(
        id="anthropic:claude-sonnet-4-5",
        name="Claude Sonnet 4.5",
        builtin_tools=["web_search", "code_execution"],
    ),
    AIModel(
        id="openai-responses:gpt-5",
        name="GPT 5",
        builtin_tools=["web_search", "code_execution", "image_generation"],
    ),
    AIModel(
        id="google-gla:gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        builtin_tools=["web_search", "code_execution"],
    ),
]


class ConfigureFrontend(BaseModel, alias_generator=to_camel, populate_by_name=True):
    """Frontend configuration response."""

    models: list[AIModel]
    builtin_tools: list[BuiltinTool]


class ChatRequestExtra(BaseModel, extra="ignore", alias_generator=to_camel):
    """Extra chat request parameters."""

    model: AIModelID | None = None
    builtin_tools: list[BuiltinToolID] = Field(default_factory=list)
    conversation_id: int


def _to_json_safe(value: Any) -> Any:
    """Convert arbitrary values into JSON-serializable structures."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        try:
            return json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return repr(value)


def _serialize_ui_parts(message: UIMessage) -> list[dict[str, Any]]:
    """Serialize UI message parts for durable storage."""
    return [_to_json_safe(part.model_dump(by_alias=True, exclude_none=True)) for part in message.parts]


def _extract_text_from_ui_message(message: UIMessage) -> str:
    """Extract full textual content from a UI message."""
    text_parts = [part.text for part in message.parts if isinstance(part, TextUIPart)]
    return "\n".join(part for part in text_parts if part).strip()


def _find_latest_user_message(messages: list[UIMessage]) -> UIMessage | None:
    """Find the latest user message from a Vercel AI message list."""
    for message in reversed(messages):
        if message.role == "user":
            return message
    return None


def _serialize_assistant_response(
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

                tool_output = _to_json_safe(part.content)
                tool_part = {
                    "type": f"tool-{part.tool_name}",
                    "toolCallId": part.tool_call_id,
                    "state": "output-available",
                    "output": tool_output,
                    "providerExecuted": False,
                }
                tool_index = tool_part_indexes.get(part.tool_call_id)
                if tool_index is not None:
                    existing_tool_part = stored_parts[tool_index]
                    existing_tool_part["state"] = "output-available"
                    existing_tool_part["output"] = tool_output
                else:
                    stored_parts.append(tool_part)
            continue

        if not isinstance(message, ModelResponse):
            continue

        for part in message.parts:
            if isinstance(part, TextPart):
                stored_parts.append({"type": "text", "text": part.content})
                if part.content:
                    content_parts.append(part.content)
                continue

            if isinstance(part, ThinkingPart):
                stored_parts.append({"type": "reasoning", "text": part.content})
                continue

            if isinstance(part, BuiltinToolCallPart):
                tool_part_indexes[part.tool_call_id] = len(stored_parts)
                stored_parts.append(
                    {
                        "type": f"tool-{part.tool_name}",
                        "toolCallId": part.tool_call_id,
                        "state": "input-available",
                        "input": part.args_as_dict(),
                        "providerExecuted": True,
                    }
                )
                continue

            if isinstance(part, ToolCallPart):
                tool_part_indexes[part.tool_call_id] = len(stored_parts)
                stored_parts.append(
                    {
                        "type": f"tool-{part.tool_name}",
                        "toolCallId": part.tool_call_id,
                        "state": "input-available",
                        "input": part.args_as_dict(),
                        "providerExecuted": False,
                    }
                )
                continue

            if isinstance(part, BuiltinToolReturnPart):
                tool_output = _to_json_safe(part.content)
                tool_part = {
                    "type": f"tool-{part.tool_name}",
                    "toolCallId": part.tool_call_id,
                    "state": "output-available",
                    "output": tool_output,
                    "providerExecuted": True,
                }
                tool_index = tool_part_indexes.get(part.tool_call_id)
                if tool_index is not None:
                    existing_tool_part = stored_parts[tool_index]
                    existing_tool_part["state"] = "output-available"
                    existing_tool_part["output"] = tool_output
                else:
                    stored_parts.append(tool_part)
                continue

            if isinstance(part, FilePart):
                stored_parts.append(
                    {
                        "type": "file",
                        "mediaType": part.content.media_type,
                        "url": part.content.data_uri,
                    }
                )
                continue

            stored_parts.append({"type": type(part).__name__, "repr": repr(part)})

    full_text = "\n".join(part for part in content_parts if part).strip()
    return [_to_json_safe(part) for part in stored_parts], full_text


async def _sync_client_message_ids(
    message_repository: MessageRepository,
    conversation_id: int,
    owner_id: int,
    ui_messages: list[UIMessage],
) -> None:
    """Backfill/align client-side message ids onto stored DB messages."""
    db_messages = await message_repository.get_by_conversation_id(
        conversation_id, include_superseded=False
    )
    db_history = [message for message in db_messages if message.role in {"user", "assistant"}]
    ui_history = [message for message in ui_messages if message.role in {"user", "assistant"}]

    for db_message, ui_message in zip(db_history, ui_history):
        if db_message.owner_id != owner_id:
            continue
        if db_message.client_message_id != ui_message.id:
            db_message.client_message_id = ui_message.id


@router.get(
    "/configure",
    response_model=ConfigureFrontend,
    summary="Get AI configuration",
    description="Get available AI models and tools for frontend configuration",
)
async def configure_frontend() -> ConfigureFrontend:
    """Get AI configuration for frontend (public endpoint)."""
    return ConfigureFrontend(
        models=AI_MODELS,
        builtin_tools=BUILTIN_TOOL_DEFS,
    )


@router.options("/stream", summary="CORS preflight for chat stream")
def options_chat():
    """Handle CORS preflight request for chat stream endpoint."""
    pass


@router.post(
    "/stream",
    summary="AI chat with streaming",
    description="Send a message to the AI and get a streaming response",
)
async def ai_chat(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    AI chat endpoint with streaming support.
    Uses Vercel AI adapter for streaming responses and supports
    multiple AI models with various built-in tools.
    """
    from ..agent import AgentDeps

    # Parse request body
    body = await request.body()
    run_input = VercelAIAdapter.build_run_input(body)
    extra_data = ChatRequestExtra.model_validate(run_input.__pydantic_extra__ or {})
    deps = AgentDeps(db=db)
    owner_id = current_user.local_user_id
    if owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user context"
        )

    conversation_repository = ConversationRepository(db)
    message_repository = MessageRepository(db)
    conversation = await conversation_repository.get_by_id(extra_data.conversation_id)
    if not conversation or conversation.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await _sync_client_message_ids(
        message_repository=message_repository,
        conversation_id=conversation.id,
        owner_id=owner_id,
        ui_messages=run_input.messages,
    )

    superseded_target: Message | None = None
    if run_input.trigger == "submit-message":
        user_message = _find_latest_user_message(run_input.messages)
        if user_message is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User message not found in request",
            )

        existing_user_message = await message_repository.get_by_client_message_id(
            conversation_id=conversation.id,
            owner_id=owner_id,
            client_message_id=user_message.id,
        )

        if existing_user_message is None:
            user_parts = _serialize_ui_parts(user_message)
            user_text = _extract_text_from_ui_message(user_message)
            if not user_text:
                user_text = json.dumps(user_parts, ensure_ascii=True)

            await message_repository.create(
                Message(
                    conversation_id=conversation.id,
                    owner_id=owner_id,
                    role="user",
                    content=user_text,
                    parts_json=user_parts,
                    client_message_id=user_message.id,
                )
            )

    elif run_input.trigger == "regenerate-message":
        superseded_target = await message_repository.get_by_client_message_id(
            conversation_id=conversation.id,
            owner_id=owner_id,
            client_message_id=run_input.message_id,
        )
        if superseded_target is None:
            superseded_target = await message_repository.get_latest_active_assistant(
                conversation_id=conversation.id, owner_id=owner_id
            )
        if superseded_target is None or superseded_target.role != "assistant":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant message not found for regeneration",
            )
    else:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported trigger '{run_input.trigger}'",
        )

    assistant_client_message_id = str(uuid4())

    async def on_complete(result: AgentRunResult[Any]) -> None:
        assistant_parts, assistant_text = _serialize_assistant_response(result)
        if not assistant_text:
            assistant_text = json.dumps(assistant_parts, ensure_ascii=True)

        assistant_message = await message_repository.create(
            Message(
                conversation_id=conversation.id,
                owner_id=owner_id,
                role="assistant",
                content=assistant_text,
                parts_json=assistant_parts,
                client_message_id=assistant_client_message_id,
            )
        )

        if superseded_target is not None:
            superseded_target.superseded_by_message_id = assistant_message.id

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(updated_at=func.now())
        )

    return await VercelAIAdapter.dispatch_request(
        request,
        agent=agent,
        deps=deps,
        model=extra_data.model,
        builtin_tools=[BUILTIN_TOOLS[tool_id] for tool_id in extra_data.builtin_tools],
        on_complete=on_complete,
    )
