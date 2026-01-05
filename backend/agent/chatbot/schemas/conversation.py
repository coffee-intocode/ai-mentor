"""Conversation schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    """Base conversation schema."""

    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation.

    Note: owner_id is not included here as it's derived from the authenticated user.
    """

    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

