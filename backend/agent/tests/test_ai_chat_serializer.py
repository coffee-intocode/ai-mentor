"""Regression tests for assistant tool-call persistence serialization."""

import unittest
from typing import Any

from pydantic_ai.messages import (
    BuiltinToolCallPart,
    BuiltinToolReturnPart,
    ModelRequest,
    ModelResponse,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
)

from chatbot.services.ai_chat import serialize_assistant_response


class _FakeResult:
    def __init__(self, messages: list[Any]):
        self._messages = messages
        self.response = ModelResponse(parts=[])

    def new_messages(self) -> list[Any]:
        return self._messages


class TestAiChatSerializer(unittest.TestCase):
    def test_function_tool_call_and_return_are_paired(self) -> None:
        result = _FakeResult(
            [
                ModelResponse(
                    parts=[
                        ToolCallPart(tool_name='retrieve', tool_call_id='call-1', args={'query': 'python'}),
                        TextPart(content='Answer text'),
                    ]
                ),
                ModelRequest(
                    parts=[
                        ToolReturnPart(
                            tool_name='retrieve',
                            tool_call_id='call-1',
                            content={'results': ['doc-1']},
                        )
                    ]
                ),
            ]
        )

        parts, full_text = serialize_assistant_response(result)

        self.assertEqual(full_text, 'Answer text')
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]['type'], 'tool-retrieve')
        self.assertEqual(parts[0]['toolCallId'], 'call-1')
        self.assertEqual(parts[0]['state'], 'output-available')
        self.assertEqual(parts[0]['input'], {'query': 'python'})
        self.assertEqual(parts[0]['output'], {'results': ['doc-1']})
        self.assertFalse(parts[0]['providerExecuted'])
        self.assertEqual(parts[1], {'type': 'text', 'text': 'Answer text'})

    def test_builtin_tool_call_and_return_are_paired(self) -> None:
        result = _FakeResult(
            [
                ModelResponse(
                    parts=[
                        ThinkingPart(content='searching'),
                        BuiltinToolCallPart(
                            tool_name='web_search',
                            tool_call_id='builtin-1',
                            args={'query': 'ai mentor'},
                        ),
                        BuiltinToolReturnPart(
                            tool_name='web_search',
                            tool_call_id='builtin-1',
                            content={'hits': [1, 2]},
                        ),
                        TextPart(content='Done'),
                    ]
                )
            ]
        )

        parts, full_text = serialize_assistant_response(result)

        self.assertEqual(full_text, 'Done')
        self.assertEqual(parts[0], {'type': 'reasoning', 'text': 'searching'})
        self.assertEqual(parts[1]['type'], 'tool-web_search')
        self.assertEqual(parts[1]['toolCallId'], 'builtin-1')
        self.assertEqual(parts[1]['state'], 'output-available')
        self.assertEqual(parts[1]['input'], {'query': 'ai mentor'})
        self.assertEqual(parts[1]['output'], {'hits': [1, 2]})
        self.assertTrue(parts[1]['providerExecuted'])
        self.assertEqual(parts[2], {'type': 'text', 'text': 'Done'})

    def test_orphan_tool_return_is_stored(self) -> None:
        result = _FakeResult(
            [
                ModelRequest(
                    parts=[
                        ToolReturnPart(
                            tool_name='retrieve',
                            tool_call_id='missing-call',
                            content={'rows': 5},
                        )
                    ]
                )
            ]
        )

        parts, full_text = serialize_assistant_response(result)

        self.assertEqual(full_text, '')
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]['type'], 'tool-retrieve')
        self.assertEqual(parts[0]['toolCallId'], 'missing-call')
        self.assertEqual(parts[0]['state'], 'output-available')
        self.assertEqual(parts[0]['output'], {'rows': 5})
        self.assertFalse(parts[0]['providerExecuted'])


if __name__ == '__main__':
    unittest.main()

