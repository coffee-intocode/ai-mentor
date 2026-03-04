"""Router-level tests for AI chat orchestration wiring."""

import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from chatbot.auth.schemas import AuthenticatedUser
from chatbot.dependencies import get_ai_chat_service, get_current_user, get_db
from chatbot.routers.ai_chat import router as ai_chat_router
from chatbot.services.ai_chat import PreparedChatRun


@dataclass
class _FakeRunInput:
    trigger: str
    messages: list[Any]
    message_id: str | None = None
    __pydantic_extra__: dict[str, Any] | None = None


class _FakeAdapter:
    run_input = _FakeRunInput(
        trigger='submit-message',
        messages=[],
        __pydantic_extra__={
            'conversationId': 55,
            'model': 'anthropic:claude-sonnet-4-5',
            'builtinTools': ['code_execution'],
        },
    )
    last_instance: '_FakeAdapter | None' = None

    def __init__(self):
        self.persisted_message_id: str | None = None
        self.run_stream_kwargs: dict[str, Any] | None = None

    @classmethod
    async def from_request(cls, request, agent):
        instance = cls()
        cls.last_instance = instance
        return instance

    def run_stream(self, **kwargs):
        self.run_stream_kwargs = kwargs
        return []

    def streaming_response(self, stream):
        return JSONResponse({'ok': True, 'persistedMessageId': self.persisted_message_id})


class _FakeChatService:
    def __init__(self):
        self.prepare_calls: list[dict[str, Any]] = []
        self.persist_calls: list[dict[str, Any]] = []
        self.raise_on_prepare: HTTPException | None = None

    async def prepare_chat_run(self, *, run_input, conversation_id: int, owner_id: int) -> PreparedChatRun:
        if self.raise_on_prepare is not None:
            raise self.raise_on_prepare
        self.prepare_calls.append(
            {
                'run_input': run_input,
                'conversation_id': conversation_id,
                'owner_id': owner_id,
            }
        )
        return PreparedChatRun(
            conversation_id=conversation_id,
            owner_id=owner_id,
            assistant_client_message_id='assistant-fixed-id',
            superseded_target_message_id=None,
        )

    async def persist_assistant_completion(self, *, prepared_run: PreparedChatRun, result):
        self.persist_calls.append({'prepared_run': prepared_run, 'result': result})


class TestAiChatRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(ai_chat_router, prefix='/api/v1')
        self.fake_service = _FakeChatService()

        async def override_get_db():
            yield object()

        self.app.dependency_overrides[get_db] = override_get_db
        self.app.dependency_overrides[get_ai_chat_service] = lambda: self.fake_service
        self.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            supabase_user_id='supabase-id',
            email='test@example.com',
            local_user_id=1,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_stream_uses_service_and_persisted_message_id(self) -> None:
        with patch('chatbot.routers.ai_chat.PersistedMessageIdVercelAIAdapter', _FakeAdapter):
            response = self.client.post('/api/v1/chat/stream', json={'messages': []})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['persistedMessageId'], 'assistant-fixed-id')
        self.assertEqual(len(self.fake_service.prepare_calls), 1)
        self.assertEqual(self.fake_service.prepare_calls[0]['conversation_id'], 55)
        self.assertEqual(self.fake_service.prepare_calls[0]['owner_id'], 1)
        self.assertIsNotNone(_FakeAdapter.last_instance)
        self.assertEqual(_FakeAdapter.last_instance.run_stream_kwargs['model'], 'anthropic:claude-sonnet-4-5')

    def test_stream_returns_401_when_user_context_missing(self) -> None:
        self.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            supabase_user_id='supabase-id',
            email='test@example.com',
            local_user_id=None,
        )
        with patch('chatbot.routers.ai_chat.PersistedMessageIdVercelAIAdapter', _FakeAdapter):
            response = self.client.post('/api/v1/chat/stream', json={'messages': []})
        self.assertEqual(response.status_code, 401)

    def test_stream_propagates_404_from_service(self) -> None:
        self.fake_service.raise_on_prepare = HTTPException(status_code=404, detail='Conversation not found')
        with patch('chatbot.routers.ai_chat.PersistedMessageIdVercelAIAdapter', _FakeAdapter):
            response = self.client.post('/api/v1/chat/stream', json={'messages': []})
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
