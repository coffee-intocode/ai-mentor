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
        self, conversation_data: ConversationCreate, owner_id: int
    ) -> Conversation:
        """Create a new conversation for the specified owner."""
        conversation = Conversation(
            owner_id=owner_id, title=conversation_data.title
        )
        return await self.repository.create(conversation)

    async def _get_authorized_conversation(
        self, conversation_id: int, owner_id: int
    ) -> Conversation:
        """Get conversation by ID, verifying ownership.

        Returns 404 for both not found and not owned to prevent ID enumeration.
        """
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation or conversation.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conversation

    async def get_conversation_by_id(
        self, conversation_id: int, owner_id: int
    ) -> Conversation:
        """Get conversation by ID, verifying ownership."""
        return await self._get_authorized_conversation(conversation_id, owner_id)

    async def get_owner_conversations(self, owner_id: int) -> List[Conversation]:
        """Get all conversations for an owner."""
        return await self.repository.get_by_owner(owner_id)

    async def update_conversation(
        self, conversation_id: int, conversation_data: ConversationUpdate, owner_id: int
    ) -> Conversation:
        """Update conversation information, verifying ownership."""
        conversation = await self._get_authorized_conversation(conversation_id, owner_id)
        update_data = conversation_data.model_dump(exclude_unset=True)
        return await self.repository.update(conversation, **update_data)

    async def delete_conversation(self, conversation_id: int, owner_id: int) -> bool:
        """Delete a conversation, verifying ownership."""
        conversation = await self._get_authorized_conversation(conversation_id, owner_id)
        return await self.repository.delete(conversation.id)

