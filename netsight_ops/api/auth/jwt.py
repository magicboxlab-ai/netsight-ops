"""JWT authentication backend for NetSight.

Tokens are signed with HMAC-SHA-256 (HS256) using a caller-supplied secret.
The :class:`JWTBackend` supports creating individual tokens and access /
refresh token pairs, and validates tokens returned by callers.

Depends on ``python-jose[cryptography]``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from netsight_ops.api.auth.context import AuthContext

_ALGORITHM = "HS256"

# Claims used inside the JWT payload
_CLAIM_SUB = "sub"
_CLAIM_USERNAME = "username"
_CLAIM_ROLES = "roles"
_CLAIM_DEVICE_SCOPES = "device_scopes"
_CLAIM_EXP = "exp"
_CLAIM_IAT = "iat"


class JWTBackend:
    """Create and validate HS256-signed JWTs.

    Args:
        secret:      HMAC signing secret.  Must be kept confidential.
        access_ttl:  Lifetime of access tokens (default 30 minutes).
        refresh_ttl: Lifetime of refresh tokens (default 7 days).

    Example::

        backend = JWTBackend(secret="my-very-secret-key")
        token = backend.create_token(
            user_id="u1",
            username="alice",
            roles=["viewer"],
            device_scopes=["fw-01"],
        )
        ctx = backend.authenticate(token)
        assert ctx is not None and ctx.username == "alice"
    """

    def __init__(
        self,
        secret: str,
        access_ttl: timedelta = timedelta(minutes=30),
        refresh_ttl: timedelta = timedelta(days=7),
    ) -> None:
        self._secret = secret
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_token(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        device_scopes: list[str],
        ttl: timedelta | None = None,
    ) -> str:
        """Encode and sign a JWT for the given principal.

        Args:
            user_id:       Unique identifier placed in the ``sub`` claim.
            username:      Login name placed in the ``username`` claim.
            roles:         Roles placed in the ``roles`` claim.
            device_scopes: Device scopes placed in the ``device_scopes`` claim.
            ttl:           Token lifetime; defaults to :attr:`_access_ttl`.

        Returns:
            A signed JWT string.
        """
        effective_ttl = ttl if ttl is not None else self._access_ttl
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            _CLAIM_SUB: user_id,
            _CLAIM_USERNAME: username,
            _CLAIM_ROLES: list(roles),
            _CLAIM_DEVICE_SCOPES: list(device_scopes),
            _CLAIM_IAT: now,
            _CLAIM_EXP: now + effective_ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def create_token_pair(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        device_scopes: list[str],
    ) -> tuple[str, str]:
        """Create an access token and a refresh token.

        Args:
            user_id:       Unique identifier for the principal.
            username:      Login name.
            roles:         Granted roles.
            device_scopes: Accessible devices.

        Returns:
            A ``(access_token, refresh_token)`` tuple.
        """
        access = self.create_token(
            user_id=user_id,
            username=username,
            roles=roles,
            device_scopes=device_scopes,
            ttl=self._access_ttl,
        )
        refresh = self.create_token(
            user_id=user_id,
            username=username,
            roles=roles,
            device_scopes=device_scopes,
            ttl=self._refresh_ttl,
        )
        return access, refresh

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def authenticate(self, token: str) -> AuthContext | None:
        """Decode and validate a JWT, returning the associated context.

        Args:
            token: A JWT string to validate.

        Returns:
            An :class:`AuthContext` if the token is valid and unexpired,
            ``None`` otherwise.
        """
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
            )
        except JWTError:
            return None

        user_id = payload.get(_CLAIM_SUB)
        username = payload.get(_CLAIM_USERNAME)
        roles = payload.get(_CLAIM_ROLES, [])
        device_scopes = payload.get(_CLAIM_DEVICE_SCOPES, [])

        if not isinstance(user_id, str) or not isinstance(username, str):
            return None

        return AuthContext(
            user_id=user_id,
            username=username,
            roles=list(roles),
            device_scopes=list(device_scopes),
        )
