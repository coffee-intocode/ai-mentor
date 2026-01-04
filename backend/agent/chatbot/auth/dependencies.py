"""FastAPI authentication dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db_session
from ..repositories import UserRepository
from .exceptions import AuthenticationError, InvalidTokenError
from .jwt import get_jwt_verifier
from .schemas import AuthenticatedUser, JWTClaims

# HTTP Bearer scheme for OpenAPI documentation
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    """Validate JWT and return authenticated user.

    Auto-creates local user record if it doesn't exist.

    Args:
        credentials: The HTTP Authorization credentials (Bearer token).
        db: Database session.

    Returns:
        AuthenticatedUser with Supabase ID, email, and local user ID.

    Raises:
        AuthenticationError: If no token provided or token is invalid.
    """
    if credentials is None:
        raise AuthenticationError('Missing authentication token')

    token = credentials.credentials
    settings = get_settings()

    if not settings.supabase_url:
        raise AuthenticationError('Supabase URL not configured')

    verifier = get_jwt_verifier(settings.supabase_url)

    # Verify token and extract claims
    claims_dict = await verifier.verify_token(token)
    claims = JWTClaims.model_validate(claims_dict)

    if not claims.email:
        raise InvalidTokenError('Token missing email claim')

    # Get or create local user
    user_repo = UserRepository(db)
    user, created = await user_repo.get_or_create_by_email(claims.email)

    if created:
        await db.commit()

    return AuthenticatedUser(
        supabase_user_id=claims.sub,
        email=claims.email,
        local_user_id=user.id,
    )


# Type alias for cleaner route signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
