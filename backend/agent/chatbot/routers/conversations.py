"""Conversation API routes."""

from fastapi import APIRouter, Depends, status

from ..dependencies import get_conversation_service, get_current_user
from ..schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from ..services import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Create a new conversation for a user",
)
async def create_conversation(
    conversation_data: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    return await service.create_conversation(conversation_data)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation by ID",
    description="Retrieve a conversation by its unique ID",
)
async def get_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get conversation by ID."""
    return await service.get_conversation_by_id(conversation_id)


@router.get(
    "/user/{user_id}",
    response_model=list[ConversationResponse],
    summary="Get user conversations",
    description="Retrieve all conversations for a specific user",
)
async def get_user_conversations(
    user_id: int, service: ConversationService = Depends(get_conversation_service)
):
    """Get all conversations for a user."""
    return await service.get_user_conversations(user_id)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation",
    description="Update conversation information (e.g., title)",
)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    """Update conversation information."""
    return await service.update_conversation(conversation_id, conversation_data)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation by ID",
)
async def delete_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation."""
    await service.delete_conversation(conversation_id)
