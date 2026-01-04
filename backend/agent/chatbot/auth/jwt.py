"""JWT verification using Supabase JWKS endpoint."""

import time

import httpx
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from .exceptions import InvalidTokenError, TokenExpiredError


class JWKSVerifier:
    """Verifies JWTs using Supabase's JWKS endpoint."""

    def __init__(self, supabase_url: str):
        self.jwks_url = f'{supabase_url}/auth/v1/.well-known/jwks.json'
        self._jwks_cache: dict | None = None
        self._cache_time: float = 0
        self._cache_ttl: float = 3600  # 1 hour

    async def get_jwks(self) -> dict:
        """Fetch JWKS with caching."""
        if self._jwks_cache and (time.time() - self._cache_time) < self._cache_ttl:
            return self._jwks_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._cache_time = time.time()
            return self._jwks_cache

    async def verify_token(self, token: str) -> dict:
        """Verify JWT and return claims.

        Args:
            token: The JWT access token to verify.

        Returns:
            The decoded JWT claims.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is invalid or verification fails.
        """
        try:
            # Get the key ID from token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            if not kid:
                raise InvalidTokenError('Token missing key ID (kid)')

            # Fetch JWKS and find matching key
            jwks_data = await self.get_jwks()
            key = None
            for k in jwks_data.get('keys', []):
                if k.get('kid') == kid:
                    key = k
                    break

            if not key:
                raise InvalidTokenError('Unable to find matching signing key')

            # Construct public key and verify token
            public_key = jwk.construct(key)
            claims = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience='authenticated',  # Supabase default audience
                options={'verify_exp': True},
            )
            return claims

        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError as e:
            raise InvalidTokenError(str(e))
        except httpx.HTTPError as e:
            raise InvalidTokenError(f'Failed to fetch JWKS: {e}')


# Singleton instance (initialized on first use)
_verifier: JWKSVerifier | None = None


def get_jwt_verifier(supabase_url: str) -> JWKSVerifier:
    """Get or create JWT verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = JWKSVerifier(supabase_url)
    return _verifier
