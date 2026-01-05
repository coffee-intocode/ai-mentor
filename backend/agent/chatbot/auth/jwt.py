"""JWT verification for Supabase authentication using asymmetric signing keys.

Supabase uses asymmetric signing keys (ES256/RS256) with public key discovery
via the JWKS endpoint. This allows fast, local JWT verification without
hitting the Auth server.

See: https://supabase.com/docs/guides/auth/jwts
"""

import jwt
from jwt import PyJWKClient

from .exceptions import InvalidTokenError, TokenExpiredError

# Supported asymmetric algorithms (Supabase signing keys)
SUPPORTED_ALGORITHMS = ['ES256', 'RS256']


class JWTVerifier:
    """Verifies JWTs using Supabase's JWKS endpoint.

    Uses PyJWKClient which automatically:
    - Fetches public keys from JWKS endpoint
    - Caches keys (default 5 minutes, configurable)
    - Matches keys by 'kid' header
    """

    def __init__(self, supabase_url: str):
        self.supabase_url = supabase_url
        self.jwks_url = f'{supabase_url}/auth/v1/.well-known/jwks.json'
        self._jwks_client = PyJWKClient(self.jwks_url, cache_keys=True, lifespan=300)

    async def verify_token(self, token: str) -> dict:
        """Verify JWT and return claims.

        Args:
            token: The JWT access token from Supabase Auth.

        Returns:
            The decoded JWT claims (sub, email, role, etc.).

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is invalid or verification fails.
        """
        try:
            # Get the signing key from JWKS (matched by 'kid' in token header)
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=SUPPORTED_ALGORITHMS,
                audience='authenticated',
                issuer=f'{self.supabase_url}/auth/v1',
            )
            return claims

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidAudienceError:
            raise InvalidTokenError('Invalid audience')
        except jwt.InvalidIssuerError:
            raise InvalidTokenError('Invalid issuer')
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(str(e))
        except Exception:
            raise InvalidTokenError('Token verification failed')


# Singleton instance
_verifier: JWTVerifier | None = None


def get_jwt_verifier(supabase_url: str) -> JWTVerifier:
    """Get or create JWT verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = JWTVerifier(supabase_url)
    return _verifier
