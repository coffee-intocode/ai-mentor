"""User API routes."""

from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, get_current_user, get_user_service
from ..schemas.user import UserResponse
from ..services import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information",
)
async def get_current_user_info(
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
):
    """Get current authenticated user."""
    return await service.get_user_by_id(current_user.local_user_id)



