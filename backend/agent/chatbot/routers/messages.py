"""Message API routes."""

from fastapi import APIRouter, Depends, Query, status

from ..dependencies import CurrentUser, get_current_user, get_message_service
from ..schemas.message import MessageCreate, MessageResponse
from ..services import MessageService

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new message",
    description="Create a new message in a conversation",
)
async def create_message(
    message_data: MessageCreate,
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """Create a new message."""
    return await service.create_message(message_data, current_user.local_user_id)


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Get message by ID",
    description="Retrieve a message by its unique ID",
)
async def get_message(
    message_id: int,
    current_user: CurrentUser,
    service: MessageService = Depends(get_message_service),
):
    """Get message by ID."""
    return await service.get_message_by_id(message_id, current_user.local_user_id)


@router.get(
    "/conversation/{conversation_id}",
    response_model=list[MessageResponse],
    summary="Get conversation messages",
    description="Retrieve all messages in a conversation",
)
async def get_conversation_messages(
    conversation_id: int,
    current_user: CurrentUser,
    include_superseded: bool = Query(
        default=False,
        description="Include superseded assistant message versions for debug/replay",
    ),
    service: MessageService = Depends(get_message_service),
):
    """Get all messages in a conversation."""
    return await service.get_conversation_messages(
        conversation_id,
        current_user.local_user_id,
        include_superseded=include_superseded,
    )
