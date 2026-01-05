"""FastAPI authentication dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db_session
from ..repositories import UserRepository
from .exceptions import AuthenticationError, InvalidTokenError
from .jwt import get_jwt_verifier
from .schemas import AuthenticatedUser, JWTClaims

# OAuth2 scheme for OpenAPI documentation (adds "Authorize" button in Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token', auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    """Validate JWT and return authenticated user.

    Auto-creates local user record if it doesn't exist.

    Args:
        token: The Bearer token from Authorization header.
        db: Database session.

    Returns:
        AuthenticatedUser with Supabase ID, email, and local user ID.

    Raises:
        AuthenticationError: If no token provided or token is invalid.
    """
    if token is None:
        raise AuthenticationError('Missing authentication token')

    settings = get_settings()

    if not settings.supabase_url:
        raise AuthenticationError('Supabase URL not configured')

    verifier = get_jwt_verifier(settings.supabase_url)

    # Verify token and extract claims
    claims_dict = await verifier.verify_token(token)
    claims = JWTClaims.model_validate(claims_dict)

    if not claims.email:
        raise InvalidTokenError('Token missing email claim')

    # Get or create local user by Supabase ID
    user_repo = UserRepository(db)
    user, created = await user_repo.get_or_create_by_supabase(
        supabase_id=claims.sub,
        email=claims.email,
    )

    if created:
        await db.commit()

    return AuthenticatedUser(
        supabase_user_id=claims.sub,
        email=claims.email,
        local_user_id=user.id,
    )


# Type alias for cleaner route signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
