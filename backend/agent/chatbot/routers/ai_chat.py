"""AI chat router with pydantic-ai integration."""

from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from pydantic_ai.builtin_tools import (
    AbstractBuiltinTool,
    CodeExecutionTool,
    ImageGenerationTool,
    WebSearchTool,
)
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent import agent
from ..dependencies import CurrentUser, get_db

router = APIRouter(tags=["ai-chat"])


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
    builtin_tools: list[BuiltinToolID] = []


@router.get(
    "/configure",
    response_model=ConfigureFrontend,
    summary="Get AI configuration",
    description="Get available AI models and tools for frontend configuration",
)
async def configure_frontend(current_user: CurrentUser) -> ConfigureFrontend:
    """Get AI configuration for frontend (requires authentication)."""
    return ConfigureFrontend(
        models=AI_MODELS,
        builtin_tools=BUILTIN_TOOL_DEFS,
    )


@router.options("/chat", summary="CORS preflight for chat")
def options_chat():
    """Handle CORS preflight request for chat endpoint."""
    pass


@router.post(
    "/chat",
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
    extra_data = ChatRequestExtra.model_validate(run_input.__pydantic_extra__)
    deps = AgentDeps(db=db)

    return await VercelAIAdapter.dispatch_request(
        request,
        agent=agent,
        deps=deps,
        model=extra_data.model,
        builtin_tools=[BUILTIN_TOOLS[tool_id] for tool_id in extra_data.builtin_tools],
    )
