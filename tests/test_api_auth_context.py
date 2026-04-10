"""Tests for netsight_ops.api.auth.context — AuthContext."""

from __future__ import annotations

import pytest

from netsight_ops.api.auth.context import AuthContext


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestAuthContextCreation:
    def test_basic_creation(self) -> None:
        ctx = AuthContext(
            user_id="u1",
            username="alice",
            roles=["viewer"],
            device_scopes=["fw-01"],
        )
        assert ctx.user_id == "u1"
        assert ctx.username == "alice"
        assert ctx.roles == ["viewer"]
        assert ctx.device_scopes == ["fw-01"]

    def test_is_frozen(self) -> None:
        """AuthContext is a frozen dataclass — mutation must raise."""
        ctx = AuthContext(
            user_id="u1",
            username="alice",
            roles=["viewer"],
            device_scopes=["fw-01"],
        )
        with pytest.raises((AttributeError, TypeError)):
            ctx.username = "bob"  # type: ignore[misc]

    def test_empty_roles_and_scopes(self) -> None:
        ctx = AuthContext(user_id="u2", username="bob", roles=[], device_scopes=[])
        assert ctx.roles == []
        assert ctx.device_scopes == []


# ---------------------------------------------------------------------------
# has_device_access
# ---------------------------------------------------------------------------


class TestHasDeviceAccess:
    def test_access_to_listed_device(self) -> None:
        ctx = AuthContext(
            user_id="u1", username="alice", roles=[], device_scopes=["fw-01", "fw-02"]
        )
        assert ctx.has_device_access("fw-01") is True
        assert ctx.has_device_access("fw-02") is True

    def test_no_access_to_unlisted_device(self) -> None:
        ctx = AuthContext(
            user_id="u1", username="alice", roles=[], device_scopes=["fw-01"]
        )
        assert ctx.has_device_access("fw-99") is False

    def test_wildcard_grants_all_devices(self) -> None:
        ctx = AuthContext(
            user_id="u1", username="alice", roles=[], device_scopes=["*"]
        )
        assert ctx.has_device_access("fw-01") is True
        assert ctx.has_device_access("any-device-name") is True

    def test_empty_scopes_denies_all(self) -> None:
        ctx = AuthContext(user_id="u1", username="alice", roles=[], device_scopes=[])
        assert ctx.has_device_access("fw-01") is False

    def test_wildcard_mixed_with_others(self) -> None:
        """Wildcard anywhere in the list should grant access."""
        ctx = AuthContext(
            user_id="u1", username="alice", roles=[], device_scopes=["fw-01", "*"]
        )
        assert ctx.has_device_access("any-device") is True


# ---------------------------------------------------------------------------
# is_admin property
# ---------------------------------------------------------------------------


class TestIsAdmin:
    def test_admin_role_grants_is_admin(self) -> None:
        ctx = AuthContext(
            user_id="u1", username="alice", roles=["admin"], device_scopes=[]
        )
        assert ctx.is_admin is True

    def test_no_admin_role(self) -> None:
        ctx = AuthContext(
            user_id="u1", username="alice", roles=["viewer", "operator"], device_scopes=[]
        )
        assert ctx.is_admin is False

    def test_empty_roles(self) -> None:
        ctx = AuthContext(user_id="u1", username="alice", roles=[], device_scopes=[])
        assert ctx.is_admin is False

    def test_admin_among_multiple_roles(self) -> None:
        ctx = AuthContext(
            user_id="u1",
            username="alice",
            roles=["viewer", "admin", "operator"],
            device_scopes=[],
        )
        assert ctx.is_admin is True
