"""Authentication schemas for JWT claims and user context."""

from pydantic import BaseModel, ConfigDict, EmailStr


class JWTClaims(BaseModel):
    """Supabase JWT token claims."""

    model_config = ConfigDict(extra='allow')

    sub: str  # User UUID from Supabase auth.users
    email: EmailStr | None = None
    aud: str  # Audience (typically "authenticated")
    exp: int  # Expiration timestamp
    iat: int | None = None  # Issued at timestamp
    role: str | None = None  # User role


class AuthenticatedUser(BaseModel):
    """Represents the authenticated user context available in route handlers."""

    supabase_user_id: str  # UUID from Supabase auth.users
    email: str
    local_user_id: int | None = None  # ID from local users table (set after DB lookup)
