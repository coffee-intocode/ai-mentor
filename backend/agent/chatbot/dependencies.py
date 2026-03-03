"""Dependency injection for FastAPI."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db_session
from .services import (
    ConversationService,
    MessageService,
    UserService,
)


# Database session dependency (already defined in database.py but re-exported here)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


# Service dependencies
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service dependency."""
    return UserService(db)


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Get conversation service dependency."""
    return ConversationService(db)


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Get message service dependency."""
    return MessageService(db)


# Re-export auth dependencies for convenience
from .auth import CurrentUser, get_current_user  # noqa: E402

__all__ = [
    'get_db',
    'get_user_service',
    'get_conversation_service',
    'get_message_service',
    'get_current_user',
    'CurrentUser',
]
