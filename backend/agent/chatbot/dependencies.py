"""Dependency injection for FastAPI."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db_session
from .services import (
    ChatService,
    ConversationService,
    MessageService,
    ReductoService,
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


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Get chat service dependency."""
    return ChatService(db)


def get_reducto_service(db: AsyncSession = Depends(get_db)) -> ReductoService:
    """Get reducto service dependency."""
    return ReductoService(db)
