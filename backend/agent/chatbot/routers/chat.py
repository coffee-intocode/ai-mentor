"""Chat API routes for integrated chat functionality."""

from fastapi import APIRouter, Depends, status

from ..dependencies import get_chat_service
from ..schemas.chat import ChatRequest, ChatResponse
from ..services import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Send a message and get an AI response, creating or using an existing conversation",
)
async def chat(
    chat_data: ChatRequest, service: ChatService = Depends(get_chat_service)
):
    """Process a chat message and return AI response."""
    return await service.process_chat(chat_data)
