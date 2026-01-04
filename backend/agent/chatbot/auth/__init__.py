"""Authentication module for Supabase JWT verification."""

from .dependencies import CurrentUser, get_current_user
from .exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError
from .schemas import AuthenticatedUser, JWTClaims

__all__ = [
    'CurrentUser',
    'get_current_user',
    'AuthenticatedUser',
    'JWTClaims',
    'AuthenticationError',
    'InvalidTokenError',
    'TokenExpiredError',
]
