"""User service for business logic."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..repositories import UserRepository
from ..schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user business logic."""

    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if await self.repository.exists_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user = User(email=user_data.email, username=user_data.username)
        return await self.repository.create(user)

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        user = await self.repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        user = await self.get_user_by_id(user_id)
        update_data = user_data.model_dump(exclude_unset=True)
        return await self.repository.update(user, **update_data)

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_user_by_id(user_id)  # Verify user exists
        return await self.repository.delete(user.id)

