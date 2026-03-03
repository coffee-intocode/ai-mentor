"""Regression tests for deterministic stream/DB assistant message ids."""

import unittest

from pydantic_ai.ui.vercel_ai.request_types import SubmitMessage

from chatbot.agent import agent
from chatbot.routers.ai_chat import PersistedMessageIdVercelAIAdapter


class TestAiChatStreamIds(unittest.IsolatedAsyncioTestCase):
    async def test_start_chunk_uses_persisted_message_id(self) -> None:
        run_input = SubmitMessage(id='chat-1', messages=[])
        adapter = PersistedMessageIdVercelAIAdapter(
            agent=agent,
            run_input=run_input,
            persisted_message_id='assistant-msg-1',
        )

        stream = adapter.build_event_stream()
        chunks = [chunk async for chunk in stream.before_stream()]

        self.assertEqual(stream.message_id, 'assistant-msg-1')
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].type, 'start')
        self.assertEqual(chunks[0].message_id, 'assistant-msg-1')


if __name__ == '__main__':
    unittest.main()

