"""Authentication context — a lightweight, immutable identity carrier.

An :class:`AuthContext` is created by each authentication backend after
successfully validating credentials or a token.  It is then attached to the
request state and used throughout the request lifecycle for authorisation
decisions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContext:
    """Immutable container for the authenticated principal's identity.

    Attributes:
        user_id:       Unique identifier for the user (e.g. a UUID or LDAP DN).
        username:      Human-readable login name.
        roles:         List of role names granted to this user.
        device_scopes: List of device names this user may access.
                       A single ``"*"`` entry grants access to all devices.
    """

    user_id: str
    username: str
    roles: list[str]
    device_scopes: list[str]

    def has_device_access(self, device_name: str) -> bool:
        """Return ``True`` if this principal may access *device_name*.

        Access is granted when the device scope list contains ``"*"`` (wildcard)
        or the exact *device_name*.

        Args:
            device_name: The name of the network device to check.

        Returns:
            ``True`` if access is permitted, ``False`` otherwise.
        """
        return "*" in self.device_scopes or device_name in self.device_scopes

    @property
    def is_admin(self) -> bool:
        """``True`` when the principal holds the ``"admin"`` role."""
        return "admin" in self.roles
