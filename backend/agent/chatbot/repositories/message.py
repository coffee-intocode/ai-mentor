"""Message repository for message-specific database operations."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Message
from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Message, db)

    async def get_by_conversation_id(self, conversation_id: int) -> List[Message]:
        """Get all messages for a specific conversation."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

