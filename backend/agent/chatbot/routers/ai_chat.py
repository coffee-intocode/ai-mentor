"""AI chat router with pydantic-ai integration."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, ValidationError
from pydantic.alias_generators import to_camel
from pydantic_ai.builtin_tools import (
    AbstractBuiltinTool,
    CodeExecutionTool,
    ImageGenerationTool,
    WebSearchTool,
)
from pydantic_ai.run import AgentRunResult
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from pydantic_ai.ui.vercel_ai._event_stream import VercelAIEventStream
from pydantic_ai.ui.vercel_ai.response_types import BaseChunk, StartChunk
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent import agent
from ..dependencies import CurrentUser, get_ai_chat_service, get_db
from ..services import AiChatService

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


@dataclass
class PersistedMessageIdEventStream(VercelAIEventStream):
    """Event stream that emits a deterministic assistant message id in the start chunk."""

    async def before_stream(self) -> AsyncIterator[BaseChunk]:
        yield StartChunk(message_id=self.message_id)


@dataclass
class PersistedMessageIdVercelAIAdapter(VercelAIAdapter):
    """Vercel adapter that forces a server-selected assistant message id."""

    persisted_message_id: str | None = None

    def build_event_stream(self) -> PersistedMessageIdEventStream:
        stream = PersistedMessageIdEventStream(self.run_input, accept=self.accept)
        if self.persisted_message_id:
            stream.message_id = self.persisted_message_id
        return stream


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


@router.post(
    "/stream",
    summary="AI chat with streaming",
    description="Send a message to the AI and get a streaming response",
)
async def ai_chat(
    request: Request,
    current_user: CurrentUser,
    chat_service: AiChatService = Depends(get_ai_chat_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    AI chat endpoint with streaming support.
    Uses Vercel AI adapter for streaming responses and supports
    multiple AI models with various built-in tools.
    """
    from ..agent import AgentDeps

    try:
        adapter = await PersistedMessageIdVercelAIAdapter.from_request(request, agent=agent)
    except ValidationError as e:  # pragma: no cover
        return Response(
            content=e.json(),
            media_type="application/json",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    run_input = adapter.run_input
    extra_data = ChatRequestExtra.model_validate(run_input.__pydantic_extra__ or {})
    deps = AgentDeps(db=db)
    owner_id = current_user.local_user_id
    if owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user context"
        )

    prepared_run = await chat_service.prepare_chat_run(
        run_input=run_input,
        conversation_id=extra_data.conversation_id,
        owner_id=owner_id,
    )
    adapter.persisted_message_id = prepared_run.assistant_client_message_id

    async def on_complete(result: AgentRunResult[Any]) -> None:
        await chat_service.persist_assistant_completion(
            prepared_run=prepared_run,
            result=result,
        )

    return adapter.streaming_response(
        adapter.run_stream(
            deps=deps,
            model=extra_data.model,
            builtin_tools=[BUILTIN_TOOLS[tool_id] for tool_id in extra_data.builtin_tools],
            on_complete=on_complete,
        )
    )
