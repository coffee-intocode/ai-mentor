"""Conversation API routes."""

from fastapi import APIRouter, Depends, status

from ..dependencies import CurrentUser, get_conversation_service, get_current_user
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


@router.get(
    "",
    response_model=list[ConversationResponse],
    summary="List my conversations",
    description="Retrieve all conversations for the current user",
)
async def list_my_conversations(
    current_user: CurrentUser,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get all conversations for the current user."""
    return await service.get_owner_conversations(current_user.local_user_id)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Create a new conversation for the current user",
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: CurrentUser,
    service: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    return await service.create_conversation(conversation_data, current_user.local_user_id)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation by ID",
    description="Retrieve a conversation by its unique ID",
)
async def get_conversation(
    conversation_id: int,
    current_user: CurrentUser,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get conversation by ID."""
    return await service.get_conversation_by_id(conversation_id, current_user.local_user_id)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation",
    description="Update conversation information (e.g., title)",
)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    current_user: CurrentUser,
    service: ConversationService = Depends(get_conversation_service),
):
    """Update conversation information."""
    return await service.update_conversation(
        conversation_id, conversation_data, current_user.local_user_id
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation by ID",
)
async def delete_conversation(
    conversation_id: int,
    current_user: CurrentUser,
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation."""
    await service.delete_conversation(conversation_id, current_user.local_user_id)
