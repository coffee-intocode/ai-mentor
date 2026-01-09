import logging
from dataclasses import dataclass
from typing import Any, cast

from dotenv import load_dotenv

load_dotenv()

import pydantic_ai
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession

from .services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


@dataclass
class AgentDeps:
    """Dependencies for the RAG agent."""

    db: AsyncSession


agent = Agent(
    "anthropic:claude-sonnet-4-5",
    deps_type=AgentDeps,
    instructions="""You are an AI mentor assistant that is ai an version of Paul Graham. Respond as if you are Paul Graham. Use the `retrieve` 
    tool to search through uploaded documents and learning materials to answer questions in the likeness Paul Graham.
    The tool performs semantic search across document sections. ALWAYS cite the source documents when providing answers in
    bottom of the response.
    If you are not sure about an answer simply reply that you don not know.""",
)


@agent.tool
async def retrieve(context: RunContext[AgentDeps], search_query: str) -> str:
    """Retrieve relevant document sections based on a search query.

    Args:
        context: The call context with dependencies
        search_query: The search query to find relevant information

    Returns:
        Formatted string with relevant document sections
    """
    from .database import AsyncSessionLocal

    logger.info(f'retrieve tool called: query={search_query[:100]}')

    try:
        # Create a fresh session for the tool since streaming closes the original
        async with AsyncSessionLocal() as session:
            logger.info('retrieve tool: session created')
            retrieval_service = RetrievalService(session)
            result = await retrieval_service.retrieve(search_query)
            logger.info(f'retrieve tool: completed, result_length={len(result)}')
            return result
    except Exception as e:
        logger.exception(f'retrieve tool: exception - {type(e).__name__}: {e}')
        raise


if __name__ == "__main__":
    # print(agent.run_sync('how do i see errors').output)
    # search_docs("logfire", "errors debugging view errors logs")
    agent.to_cli_sync()
