"""Message schemas for request/response validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


MessageRole = Literal["user", "assistant", "system"]


class MessageBase(BaseModel):
    """Base message schema."""

    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    conversation_id: int
    parts_json: list[dict[str, Any]] | None = None
    client_message_id: str | None = None


class MessageResponse(MessageBase):
    """Schema for message responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    owner_id: int
    parts_json: list[dict[str, Any]]
    client_message_id: str | None = None
    superseded_by_message_id: int | None = None
    created_at: datetime
