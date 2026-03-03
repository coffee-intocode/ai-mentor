"""Service-level regression tests for chat persistence flows."""

import unittest
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage

from chatbot.models import Conversation, Message
from chatbot.services.ai_chat import AiChatService


class _FakeDbSession:
    def __init__(self):
        self.executed: list[Any] = []

    async def execute(self, statement: Any) -> None:
        self.executed.append(statement)


class _FakeConversationRepository:
    def __init__(self, conversations: dict[int, Conversation]):
        self.conversations = conversations

    async def get_by_id(self, conversation_id: int) -> Conversation | None:
        return self.conversations.get(conversation_id)


class _FakeMessageRepository:
    def __init__(self, messages: list[Message] | None = None):
        self.messages = messages or []
        self._next_id = max((message.id or 0 for message in self.messages), default=0) + 1

    async def create(self, message: Message) -> Message:
        if message.id is None:
            message.id = self._next_id
            self._next_id += 1
        self.messages.append(message)
        return message

    async def get_by_client_message_id(
        self, conversation_id: int, owner_id: int, client_message_id: str
    ) -> Message | None:
        for message in self.messages:
            if (
                message.conversation_id == conversation_id
                and message.owner_id == owner_id
                and message.client_message_id == client_message_id
            ):
                return message
        return None


class _FakeResult:
    def __init__(self, messages: list[Any]):
        self._messages = messages
        self.response = ModelResponse(parts=[])

    def new_messages(self) -> list[Any]:
        return self._messages


@dataclass
class _FakeRunInput:
    trigger: str
    messages: list[UIMessage]
    message_id: str | None = None


def _conversation(conversation_id: int, owner_id: int) -> Conversation:
    conversation = Conversation(owner_id=owner_id, title='Test')
    conversation.id = conversation_id
    return conversation


def _assistant_message(
    message_id: int,
    *,
    conversation_id: int,
    owner_id: int,
    client_message_id: str,
) -> Message:
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        owner_id=owner_id,
        role='assistant',
        content='Existing assistant',
        parts_json=[{'type': 'text', 'text': 'Existing assistant'}],
        client_message_id=client_message_id,
    )
    return message


class TestAiChatService(unittest.IsolatedAsyncioTestCase):
    async def test_submit_then_complete_persists_user_and_assistant(self) -> None:
        db = _FakeDbSession()
        conversation_repo = _FakeConversationRepository({10: _conversation(10, 1)})
        message_repo = _FakeMessageRepository()
        service = AiChatService(
            db,
            conversation_repository=conversation_repo,
            message_repository=message_repo,
        )

        run_input = _FakeRunInput(
            trigger='submit-message',
            messages=[
                UIMessage(
                    id='user-1',
                    role='user',
                    parts=[TextUIPart(text='How do I debug this?')],
                )
            ],
        )

        prepared = await service.prepare_chat_run(
            run_input=run_input,
            conversation_id=10,
            owner_id=1,
        )
        self.assertEqual(len(message_repo.messages), 1)
        self.assertEqual(message_repo.messages[0].role, 'user')
        self.assertEqual(message_repo.messages[0].client_message_id, 'user-1')

        assistant_result = _FakeResult([ModelResponse(parts=[TextPart(content='Start with logs.')])])
        assistant_message = await service.persist_assistant_completion(
            prepared_run=prepared,
            result=assistant_result,
        )

        self.assertEqual(len(message_repo.messages), 2)
        self.assertEqual(assistant_message.role, 'assistant')
        self.assertEqual(assistant_message.content, 'Start with logs.')
        self.assertEqual(assistant_message.client_message_id, prepared.assistant_client_message_id)
        self.assertGreater(len(db.executed), 0)

    async def test_submit_is_idempotent_for_same_user_message_id(self) -> None:
        db = _FakeDbSession()
        conversation_repo = _FakeConversationRepository({10: _conversation(10, 1)})
        message_repo = _FakeMessageRepository()
        service = AiChatService(
            db,
            conversation_repository=conversation_repo,
            message_repository=message_repo,
        )

        run_input = _FakeRunInput(
            trigger='submit-message',
            messages=[UIMessage(id='user-1', role='user', parts=[TextUIPart(text='Hello')])],
        )

        await service.prepare_chat_run(run_input=run_input, conversation_id=10, owner_id=1)
        await service.prepare_chat_run(run_input=run_input, conversation_id=10, owner_id=1)

        self.assertEqual(len(message_repo.messages), 1)
        self.assertEqual(message_repo.messages[0].client_message_id, 'user-1')

    async def test_regenerate_supersedes_target_assistant_message(self) -> None:
        db = _FakeDbSession()
        conversation_repo = _FakeConversationRepository({10: _conversation(10, 1)})
        previous_assistant = _assistant_message(
            7,
            conversation_id=10,
            owner_id=1,
            client_message_id='assistant-old',
        )
        message_repo = _FakeMessageRepository(messages=[previous_assistant])
        service = AiChatService(
            db,
            conversation_repository=conversation_repo,
            message_repository=message_repo,
        )

        run_input = _FakeRunInput(
            trigger='regenerate-message',
            message_id='assistant-old',
            messages=[],
        )

        prepared = await service.prepare_chat_run(
            run_input=run_input,
            conversation_id=10,
            owner_id=1,
        )
        await service.persist_assistant_completion(
            prepared_run=prepared,
            result=_FakeResult([ModelResponse(parts=[TextPart(content='Rewritten answer')])]),
        )

        self.assertEqual(len(message_repo.messages), 2)
        replacement = message_repo.messages[-1]
        self.assertEqual(replacement.role, 'assistant')
        self.assertEqual(previous_assistant.superseded_by_message_id, replacement.id)

    async def test_prepare_requires_conversation_ownership(self) -> None:
        db = _FakeDbSession()
        conversation_repo = _FakeConversationRepository({10: _conversation(10, 2)})
        service = AiChatService(
            db,
            conversation_repository=conversation_repo,
            message_repository=_FakeMessageRepository(),
        )

        run_input = _FakeRunInput(
            trigger='submit-message',
            messages=[UIMessage(id='user-1', role='user', parts=[TextUIPart(text='hello')])],
        )

        with self.assertRaises(HTTPException) as ctx:
            await service.prepare_chat_run(
                run_input=run_input,
                conversation_id=10,
                owner_id=1,
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_regenerate_requires_existing_assistant_client_message_id(self) -> None:
        db = _FakeDbSession()
        conversation_repo = _FakeConversationRepository({10: _conversation(10, 1)})
        service = AiChatService(
            db,
            conversation_repository=conversation_repo,
            message_repository=_FakeMessageRepository(),
        )

        with self.assertRaises(HTTPException) as ctx:
            await service.prepare_chat_run(
                run_input=_FakeRunInput(
                    trigger='regenerate-message',
                    message_id='missing-assistant',
                    messages=[],
                ),
                conversation_id=10,
                owner_id=1,
            )
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == '__main__':
    unittest.main()

