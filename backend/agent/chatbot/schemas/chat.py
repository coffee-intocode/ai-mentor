"""Chat schemas for integrated chat functionality."""

from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Schema for chat requests."""

    message: str
    user_id: int
    conversation_id: Optional[int] = None


class MessageInResponse(BaseModel):
    """Schema for message details in chat response."""

    id: int
    content: str


class ChatResponse(BaseModel):
    """Schema for chat responses."""

    conversation_id: int
    user_message: MessageInResponse
    assistant_message: MessageInResponse

