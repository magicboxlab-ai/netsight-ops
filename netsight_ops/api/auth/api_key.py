"""API-key authentication backend for NetSight.

Keys are stored in-memory as an opaque mapping from key string to a frozen
:class:`_StoredKey` record.  Production deployments should replace or extend
:class:`APIKeyBackend` to persist keys in a secrets store.
"""

from __future__ import annotations

from dataclasses import dataclass

from netsight_ops.api.auth.context import AuthContext


@dataclass(frozen=True)
class _StoredKey:
    """Internal record associated with a registered API key.

    Not part of the public API.
    """

    user_id: str
    username: str
    roles: list[str]
    device_scopes: list[str]


class APIKeyBackend:
    """In-memory store that validates, adds, and revokes API keys.

    Example::

        backend = APIKeyBackend()
        backend.add_key(
            key="secret-key-abc",
            user_id="u1",
            username="alice",
            roles=["viewer"],
            device_scopes=["fw-01"],
        )
        ctx = backend.authenticate("secret-key-abc")
        assert ctx is not None and ctx.username == "alice"
    """

    def __init__(self) -> None:
        self._keys: dict[str, _StoredKey] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_key(
        self,
        key: str,
        user_id: str,
        username: str,
        roles: list[str],
        device_scopes: list[str],
    ) -> None:
        """Register a new API key.

        Args:
            key:           The raw API key string (treat as a secret).
            user_id:       Unique identifier for the owner.
            username:      Human-readable login name.
            roles:         Role names granted to this key's owner.
            device_scopes: Device names accessible via this key.
        """
        self._keys[key] = _StoredKey(
            user_id=user_id,
            username=username,
            roles=list(roles),
            device_scopes=list(device_scopes),
        )

    def revoke_key(self, key: str) -> None:
        """Remove a key from the store.

        Silently ignores keys that are not registered.

        Args:
            key: The API key to revoke.
        """
        self._keys.pop(key, None)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self, key: str) -> AuthContext | None:
        """Validate *key* and return the associated :class:`AuthContext`.

        Args:
            key: The API key presented by the caller.

        Returns:
            An :class:`AuthContext` if the key is known, ``None`` otherwise.
        """
        stored = self._keys.get(key)
        if stored is None:
            return None
        return AuthContext(
            user_id=stored.user_id,
            username=stored.username,
            roles=list(stored.roles),
            device_scopes=list(stored.device_scopes),
        )
