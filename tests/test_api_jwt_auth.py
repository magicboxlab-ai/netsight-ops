"""Tests for netsight_ops.api.auth.jwt — JWTBackend."""

from __future__ import annotations

from datetime import timedelta

import pytest

from netsight_ops.api.auth.context import AuthContext
from netsight_ops.api.auth.jwt import JWTBackend


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def backend() -> JWTBackend:
    return JWTBackend(secret="test-secret-key-for-unit-tests")


@pytest.fixture()
def sample_token(backend: JWTBackend) -> str:
    return backend.create_token(
        user_id="u1",
        username="alice",
        roles=["viewer"],
        device_scopes=["fw-01"],
    )


# ---------------------------------------------------------------------------
# create_token
# ---------------------------------------------------------------------------


class TestJWTCreateToken:
    def test_returns_non_empty_string(self, backend: JWTBackend) -> None:
        token = backend.create_token("u1", "alice", ["viewer"], ["fw-01"])
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_three_part_jwt(self, backend: JWTBackend) -> None:
        """JWT must have three dot-separated segments."""
        token = backend.create_token("u1", "alice", [], [])
        parts = token.split(".")
        assert len(parts) == 3

    def test_different_users_produce_different_tokens(self, backend: JWTBackend) -> None:
        t1 = backend.create_token("u1", "alice", [], [])
        t2 = backend.create_token("u2", "bob", [], [])
        assert t1 != t2


# ---------------------------------------------------------------------------
# authenticate — valid token
# ---------------------------------------------------------------------------


class TestJWTAuthenticate:
    def test_valid_token_returns_auth_context(
        self, backend: JWTBackend, sample_token: str
    ) -> None:
        ctx = backend.authenticate(sample_token)
        assert ctx is not None
        assert isinstance(ctx, AuthContext)

    def test_context_user_id(self, backend: JWTBackend, sample_token: str) -> None:
        ctx = backend.authenticate(sample_token)
        assert ctx is not None
        assert ctx.user_id == "u1"

    def test_context_username(self, backend: JWTBackend, sample_token: str) -> None:
        ctx = backend.authenticate(sample_token)
        assert ctx is not None
        assert ctx.username == "alice"

    def test_context_roles(self, backend: JWTBackend, sample_token: str) -> None:
        ctx = backend.authenticate(sample_token)
        assert ctx is not None
        assert ctx.roles == ["viewer"]

    def test_context_device_scopes(self, backend: JWTBackend, sample_token: str) -> None:
        ctx = backend.authenticate(sample_token)
        assert ctx is not None
        assert ctx.device_scopes == ["fw-01"]

    def test_multiple_roles_and_scopes(self, backend: JWTBackend) -> None:
        token = backend.create_token(
            "u3", "carol", ["viewer", "operator"], ["fw-01", "fw-02"]
        )
        ctx = backend.authenticate(token)
        assert ctx is not None
        assert set(ctx.roles) == {"viewer", "operator"}
        assert set(ctx.device_scopes) == {"fw-01", "fw-02"}


# ---------------------------------------------------------------------------
# authenticate — invalid / expired tokens
# ---------------------------------------------------------------------------


class TestJWTAuthenticateInvalid:
    def test_invalid_token_returns_none(self, backend: JWTBackend) -> None:
        ctx = backend.authenticate("not.a.jwt")
        assert ctx is None

    def test_empty_string_returns_none(self, backend: JWTBackend) -> None:
        ctx = backend.authenticate("")
        assert ctx is None

    def test_wrong_secret_returns_none(self) -> None:
        backend_a = JWTBackend(secret="secret-a")
        backend_b = JWTBackend(secret="secret-b")
        token = backend_a.create_token("u1", "alice", [], [])
        ctx = backend_b.authenticate(token)
        assert ctx is None

    def test_expired_token_returns_none(self) -> None:
        backend = JWTBackend(
            secret="test-secret",
            access_ttl=timedelta(seconds=-1),  # already expired
        )
        token = backend.create_token("u1", "alice", [], [])
        ctx = backend.authenticate(token)
        assert ctx is None

    def test_tampered_token_returns_none(self, backend: JWTBackend, sample_token: str) -> None:
        # Flip the last character of the signature segment
        parts = sample_token.rsplit(".", 1)
        sig = parts[1]
        last_char = "A" if sig[-1] != "A" else "B"
        tampered = parts[0] + "." + sig[:-1] + last_char
        ctx = backend.authenticate(tampered)
        assert ctx is None


# ---------------------------------------------------------------------------
# create_token_pair
# ---------------------------------------------------------------------------


class TestJWTCreateTokenPair:
    def test_returns_tuple_of_two_strings(self, backend: JWTBackend) -> None:
        access, refresh = backend.create_token_pair("u1", "alice", ["viewer"], ["fw-01"])
        assert isinstance(access, str) and len(access) > 0
        assert isinstance(refresh, str) and len(refresh) > 0

    def test_access_and_refresh_are_different(self, backend: JWTBackend) -> None:
        access, refresh = backend.create_token_pair("u1", "alice", [], [])
        assert access != refresh

    def test_both_tokens_validate(self, backend: JWTBackend) -> None:
        access, refresh = backend.create_token_pair("u1", "alice", ["viewer"], ["*"])
        ctx_a = backend.authenticate(access)
        ctx_r = backend.authenticate(refresh)
        assert ctx_a is not None
        assert ctx_r is not None
        assert ctx_a.username == "alice"
        assert ctx_r.username == "alice"

    def test_refresh_token_has_longer_ttl(self) -> None:
        """Verify refresh token expiry is later than access token expiry."""
        from jose import jwt as jose_jwt

        backend = JWTBackend(
            secret="test-secret",
            access_ttl=timedelta(minutes=30),
            refresh_ttl=timedelta(days=7),
        )
        access, refresh = backend.create_token_pair("u1", "alice", [], [])
        access_payload = jose_jwt.get_unverified_claims(access)
        refresh_payload = jose_jwt.get_unverified_claims(refresh)
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_custom_access_ttl(self) -> None:
        backend = JWTBackend(
            secret="test-secret",
            access_ttl=timedelta(hours=1),
            refresh_ttl=timedelta(days=30),
        )
        token = backend.create_token("u1", "alice", [], [])
        ctx = backend.authenticate(token)
        assert ctx is not None
