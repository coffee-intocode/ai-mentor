"""Message service for business logic."""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Message
from ..repositories import MessageRepository, ConversationRepository
from ..schemas.message import MessageCreate


class MessageService:
    """Service for message business logic."""

    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)
        self.conversation_repository = ConversationRepository(db)

    async def create_message(self, message_data: MessageCreate) -> Message:
        """Create a new message."""
        # Verify conversation exists
        conversation = await self.conversation_repository.get_by_id(
            message_data.conversation_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        message = Message(
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content,
        )
        return await self.repository.create(message)

    async def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """Get all messages for a conversation."""
        # Verify conversation exists
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return await self.repository.get_by_conversation_id(conversation_id)

    async def get_message_by_id(self, message_id: int) -> Message:
        """Get message by ID."""
        message = await self.repository.get_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
            )
        return message

