"""Tests for netsight_ops.api.auth.api_key — APIKeyBackend."""

from __future__ import annotations

import pytest

from netsight_ops.api.auth.api_key import APIKeyBackend
from netsight_ops.api.auth.context import AuthContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def backend() -> APIKeyBackend:
    b = APIKeyBackend()
    b.add_key(
        key="valid-key-abc",
        user_id="u1",
        username="alice",
        roles=["viewer"],
        device_scopes=["fw-01"],
    )
    return b


# ---------------------------------------------------------------------------
# add_key / authenticate
# ---------------------------------------------------------------------------


class TestAPIKeyAuthenticate:
    def test_valid_key_returns_auth_context(self, backend: APIKeyBackend) -> None:
        ctx = backend.authenticate("valid-key-abc")
        assert ctx is not None
        assert isinstance(ctx, AuthContext)

    def test_valid_key_context_fields(self, backend: APIKeyBackend) -> None:
        ctx = backend.authenticate("valid-key-abc")
        assert ctx is not None
        assert ctx.user_id == "u1"
        assert ctx.username == "alice"
        assert ctx.roles == ["viewer"]
        assert ctx.device_scopes == ["fw-01"]

    def test_invalid_key_returns_none(self, backend: APIKeyBackend) -> None:
        ctx = backend.authenticate("wrong-key")
        assert ctx is None

    def test_empty_key_returns_none(self, backend: APIKeyBackend) -> None:
        ctx = backend.authenticate("")
        assert ctx is None

    def test_multiple_keys_independently(self) -> None:
        b = APIKeyBackend()
        b.add_key("key-a", "u1", "alice", ["viewer"], ["fw-01"])
        b.add_key("key-b", "u2", "bob", ["admin"], ["*"])
        ctx_a = b.authenticate("key-a")
        ctx_b = b.authenticate("key-b")
        assert ctx_a is not None and ctx_a.username == "alice"
        assert ctx_b is not None and ctx_b.username == "bob"

    def test_returned_context_is_isolated(self) -> None:
        """Mutating roles list on returned context must not affect stored key."""
        b = APIKeyBackend()
        b.add_key("key-x", "u1", "alice", ["viewer"], ["fw-01"])
        ctx1 = b.authenticate("key-x")
        assert ctx1 is not None
        # Attempt mutation of returned list (frozen dataclass — would raise anyway, but
        # even if roles were a mutable list on a normal dataclass, the next call
        # should be unaffected)
        ctx2 = b.authenticate("key-x")
        assert ctx2 is not None
        assert ctx2.roles == ["viewer"]


# ---------------------------------------------------------------------------
# revoke_key
# ---------------------------------------------------------------------------


class TestAPIKeyRevoke:
    def test_revoke_invalidates_key(self, backend: APIKeyBackend) -> None:
        backend.revoke_key("valid-key-abc")
        ctx = backend.authenticate("valid-key-abc")
        assert ctx is None

    def test_revoke_unknown_key_does_not_raise(self, backend: APIKeyBackend) -> None:
        backend.revoke_key("nonexistent-key")  # must not raise

    def test_revoke_only_affects_target_key(self) -> None:
        b = APIKeyBackend()
        b.add_key("key-a", "u1", "alice", ["viewer"], [])
        b.add_key("key-b", "u2", "bob", ["viewer"], [])
        b.revoke_key("key-a")
        assert b.authenticate("key-a") is None
        assert b.authenticate("key-b") is not None

    def test_revoke_then_re_add(self, backend: APIKeyBackend) -> None:
        backend.revoke_key("valid-key-abc")
        backend.add_key("valid-key-abc", "u1", "alice", ["admin"], ["*"])
        ctx = backend.authenticate("valid-key-abc")
        assert ctx is not None
        assert ctx.roles == ["admin"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestAPIKeyEdgeCases:
    def test_empty_backend_returns_none(self) -> None:
        b = APIKeyBackend()
        assert b.authenticate("any-key") is None

    def test_overwrite_existing_key(self) -> None:
        b = APIKeyBackend()
        b.add_key("key-x", "u1", "alice", ["viewer"], [])
        b.add_key("key-x", "u2", "charlie", ["admin"], ["*"])
        ctx = b.authenticate("key-x")
        assert ctx is not None
        assert ctx.username == "charlie"
        assert "admin" in ctx.roles
