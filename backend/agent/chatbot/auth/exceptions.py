"""Authentication exceptions."""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = 'Could not validate credentials'):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'},
        )


class TokenExpiredError(AuthenticationError):
    """Raised when the JWT token has expired."""

    def __init__(self):
        super().__init__(detail='Token has expired')


class InvalidTokenError(AuthenticationError):
    """Raised when the JWT token is invalid."""

    def __init__(self, detail: str = 'Invalid token'):
        super().__init__(detail=detail)
