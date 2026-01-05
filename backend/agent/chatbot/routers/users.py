"""User API routes."""

from fastapi import APIRouter, Depends, status

from ..dependencies import CurrentUser, get_current_user, get_user_service
from ..schemas.user import UserCreate, UserResponse, UserUpdate
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


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with email and optional username",
)
async def create_user(
    user_data: UserCreate, service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    return await service.create_user(user_data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a user by their unique ID",
)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    """Get user by ID."""
    return await service.get_user_by_id(user_id)


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
    description="Retrieve a user by their email address",
)
async def get_user_by_email(
    email: str, service: UserService = Depends(get_user_service)
):
    """Get user by email."""
    return await service.get_user_by_email(email)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    """Update user information."""
    return await service.update_user(user_id, user_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user by ID",
)
async def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    """Delete a user."""
    return await service.delete_user(user_id)
