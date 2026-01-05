"""User repository for user-specific database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        user = await self.get_by_email(email)
        return user is not None

    async def get_by_supabase_id(self, supabase_id: str) -> Optional[User]:
        """Get user by Supabase user ID."""
        result = await self.db.execute(
            select(User).where(User.supabase_user_id == supabase_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_by_supabase(
        self, supabase_id: str, email: str
    ) -> tuple[User, bool]:
        """Get existing user or create new one from Supabase auth.


        Args:
            supabase_id: The Supabase user UUID.
            email: The user's email address.

        Returns:
            Tuple of (user, created) where created is True if a new user was created.
        """
        user = await self.get_by_supabase_id(supabase_id)
        if user:
            return user, False

        # Create new user
        user = User(supabase_user_id=supabase_id, email=email)
        await self.create(user)
        return user, True
