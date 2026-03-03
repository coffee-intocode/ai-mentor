"""Regression test for guaranteed client_message_id on message writes."""

import unittest

from chatbot.models import Conversation, Message
from chatbot.schemas.message import MessageCreate
from chatbot.services.message import MessageService


class _FakeConversationRepository:
    def __init__(self, conversation: Conversation):
        self.conversation = conversation

    async def get_by_id(self, _: int) -> Conversation:
        return self.conversation


class _FakeMessageRepository:
    def __init__(self):
        self.created: list[Message] = []

    async def create(self, message: Message) -> Message:
        self.created.append(message)
        return message


def _conversation() -> Conversation:
    conversation = Conversation(owner_id=1, title='Test')
    conversation.id = 22
    return conversation


class TestMessageServiceClientIds(unittest.IsolatedAsyncioTestCase):
    async def test_create_message_generates_client_message_id_when_missing(self) -> None:
        service = MessageService(db=None)  # type: ignore[arg-type]
        service.conversation_repository = _FakeConversationRepository(_conversation())  # type: ignore[assignment]
        service.repository = _FakeMessageRepository()  # type: ignore[assignment]

        created = await service.create_message(
            MessageCreate(
                conversation_id=22,
                role='user',
                content='hello',
                client_message_id=None,
            ),
            owner_id=1,
        )

        self.assertIsNotNone(created.client_message_id)
        self.assertNotEqual(created.client_message_id, '')


if __name__ == '__main__':
    unittest.main()

