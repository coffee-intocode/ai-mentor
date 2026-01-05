"""Conversation repository for conversation-specific database operations."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Conversation
from .base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def get_by_owner(self, owner_id: int) -> List[Conversation]:
        """Get all conversations for a specific owner."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.owner_id == owner_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

