"""NetSight API authentication backends.

Provides three pluggable authentication strategies:

- :class:`~netsight_ops.api.auth.api_key.APIKeyBackend` — opaque shared secrets
- :class:`~netsight_ops.api.auth.jwt.JWTBackend` — HS256-signed JSON Web Tokens
- :class:`~netsight_ops.api.auth.oauth.OAuthBackend` — OAuth 2.0 provider registry

All backends return an :class:`~netsight_ops.api.auth.context.AuthContext` on
successful authentication.
"""

from __future__ import annotations

from netsight_ops.api.auth.api_key import APIKeyBackend
from netsight_ops.api.auth.context import AuthContext
from netsight_ops.api.auth.jwt import JWTBackend
from netsight_ops.api.auth.oauth import OAuthBackend, OAuthProvider

__all__ = [
    "AuthContext",
    "APIKeyBackend",
    "JWTBackend",
    "OAuthBackend",
    "OAuthProvider",
]
