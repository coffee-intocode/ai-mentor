"""Conversation service for business logic."""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Conversation
from ..repositories import ConversationRepository, UserRepository
from ..schemas.conversation import ConversationCreate, ConversationUpdate


class ConversationService:
    """Service for conversation business logic."""

    def __init__(self, db: AsyncSession):
        self.repository = ConversationRepository(db)
        self.user_repository = UserRepository(db)

    async def create_conversation(
        self, conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        # Verify user exists
        user = await self.user_repository.get_by_id(conversation_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        conversation = Conversation(
            user_id=conversation_data.user_id, title=conversation_data.title
        )
        return await self.repository.create(conversation)

    async def get_conversation_by_id(self, conversation_id: int) -> Conversation:
        """Get conversation by ID."""
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conversation

    async def get_user_conversations(self, user_id: int) -> List[Conversation]:
        """Get all conversations for a user."""
        # Verify user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return await self.repository.get_by_user_id(user_id)

    async def update_conversation(
        self, conversation_id: int, conversation_data: ConversationUpdate
    ) -> Conversation:
        """Update conversation information."""
        conversation = await self.get_conversation_by_id(conversation_id)
        update_data = conversation_data.model_dump(exclude_unset=True)
        return await self.repository.update(conversation, **update_data)

    async def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        conversation = await self.get_conversation_by_id(
            conversation_id
        )  # Verify exists
        return await self.repository.delete(conversation.id)

