"""Conversation schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    """Base conversation schema."""

    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""

    user_id: int


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

