"""Message repository for message-specific database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Message
from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Message, db)

    async def get_by_conversation_id(
        self, conversation_id: int, include_superseded: bool = False
    ) -> List[Message]:
        """Get all messages for a specific conversation."""
        query = select(Message).where(Message.conversation_id == conversation_id)
        if not include_superseded:
            query = query.where(Message.superseded_by_message_id.is_(None))
        result = await self.db.execute(query.order_by(Message.created_at.asc(), Message.id.asc()))
        return list(result.scalars().all())

    async def get_by_client_message_id(
        self, conversation_id: int, owner_id: int, client_message_id: str
    ) -> Optional[Message]:
        """Get a message by the client-side message id in a conversation."""
        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.owner_id == owner_id,
                Message.client_message_id == client_message_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_active_assistant(
        self, conversation_id: int, owner_id: int
    ) -> Optional[Message]:
        """Get the latest non-superseded assistant message in a conversation."""
        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.owner_id == owner_id,
                Message.role == "assistant",
                Message.superseded_by_message_id.is_(None),
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
