"""Message schemas for request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


MessageRole = Literal["user", "assistant", "system"]


class MessageBase(BaseModel):
    """Base message schema."""

    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    conversation_id: int


class MessageResponse(MessageBase):
    """Schema for message responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    owner_id: int
    created_at: datetime

