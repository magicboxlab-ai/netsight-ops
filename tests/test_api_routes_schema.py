"""Tests for netsight_ops.api.routes.schema, plugins, and server configuration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from netsight_ops.api.server import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a test client for the NetSight FastAPI application."""
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Swagger / ReDoc documentation endpoints
# ---------------------------------------------------------------------------


class TestDocumentationEndpoints:
    def test_swagger_docs(self, client: TestClient) -> None:
        """GET /docs must return HTTP 200 (Swagger UI)."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc(self, client: TestClient) -> None:
        """GET /redoc must return HTTP 200 (ReDoc UI)."""
        response = client.get("/redoc")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/plugins
# ---------------------------------------------------------------------------


class TestListPlugins:
    def test_returns_200(self, client: TestClient) -> None:
        """Listing plugins must return HTTP 200."""
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200

    def test_response_status_is_success(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.get("/api/v1/plugins")
        body = response.json()
        assert body["status"] == "ok"

    def test_data_contains_paloalto_pack(self, client: TestClient) -> None:
        """paloalto-firewall-xml pack must be auto-registered and present in the list."""
        response = client.get("/api/v1/plugins")
        body = response.json()
        plugin_names = [p["name"] for p in body["data"]]
        assert "paloalto-firewall-xml" in plugin_names

    def test_data_is_list(self, client: TestClient) -> None:
        """Response data must be a list of plugin records."""
        response = client.get("/api/v1/plugins")
        body = response.json()
        assert isinstance(body["data"], list)

    def test_plugin_record_has_name_field(self, client: TestClient) -> None:
        """Each plugin record in data must expose a 'name' field."""
        response = client.get("/api/v1/plugins")
        body = response.json()
        for plugin in body["data"]:
            assert "name" in plugin


# ---------------------------------------------------------------------------
# GET /api/v1/schema/operations
# ---------------------------------------------------------------------------


class TestOperationsSchema:
    def test_returns_200(self, client: TestClient) -> None:
        """Schema operations endpoint must return HTTP 200."""
        response = client.get("/api/v1/schema/operations")
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.get("/api/v1/schema/operations")
        body = response.json()
        assert body["status"] == "ok"

    def test_data_has_tools_key(self, client: TestClient) -> None:
        """Response data must contain a 'tools' key (from export_full_catalog)."""
        response = client.get("/api/v1/schema/operations")
        body = response.json()
        assert "tools" in body["data"]

    def test_data_has_patterns_key(self, client: TestClient) -> None:
        """Response data must contain a 'patterns' key."""
        response = client.get("/api/v1/schema/operations")
        body = response.json()
        assert "patterns" in body["data"]

    def test_data_has_relations_key(self, client: TestClient) -> None:
        """Response data must contain a 'relations' key."""
        response = client.get("/api/v1/schema/operations")
        body = response.json()
        assert "relations" in body["data"]

    def test_tools_is_list(self, client: TestClient) -> None:
        """The 'tools' value in data must be a list."""
        response = client.get("/api/v1/schema/operations")
        body = response.json()
        assert isinstance(body["data"]["tools"], list)
