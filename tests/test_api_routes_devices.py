"""Tests for netsight_ops.api.routes.devices — device-related REST endpoints."""

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
# GET /api/v1/devices
# ---------------------------------------------------------------------------


class TestListDevices:
    def test_returns_200(self, client: TestClient) -> None:
        """Listing devices must return HTTP 200."""
        response = client.get("/api/v1/devices")
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.get("/api/v1/devices")
        body = response.json()
        assert body["status"] == "ok"

    def test_data_is_list(self, client: TestClient) -> None:
        """Response data must be a list (even if empty)."""
        response = client.get("/api/v1/devices")
        body = response.json()
        assert isinstance(body["data"], list)

    def test_response_has_metadata(self, client: TestClient) -> None:
        """Response envelope must contain a metadata block."""
        response = client.get("/api/v1/devices")
        body = response.json()
        assert "metadata" in body


# ---------------------------------------------------------------------------
# GET /api/v1/devices/{name}/info
# ---------------------------------------------------------------------------


class TestDeviceInfo:
    def test_returns_200(self, client: TestClient) -> None:
        """Device info endpoint must return HTTP 200."""
        response = client.get("/api/v1/devices/test-fw-01/info")
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.get("/api/v1/devices/test-fw-01/info")
        body = response.json()
        assert body["status"] == "ok"

    def test_device_name_in_response(self, client: TestClient) -> None:
        """Response envelope must include the device name supplied in the path."""
        response = client.get("/api/v1/devices/test-fw-01/info")
        body = response.json()
        assert body["device"] == "test-fw-01"


# ---------------------------------------------------------------------------
# GET /api/v1/devices/{name}/operations
# ---------------------------------------------------------------------------


class TestListDeviceOperations:
    def test_returns_200(self, client: TestClient) -> None:
        """List-operations endpoint must return HTTP 200."""
        response = client.get("/api/v1/devices/test-fw-01/operations")
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.get("/api/v1/devices/test-fw-01/operations")
        body = response.json()
        assert body["status"] == "ok"

    def test_data_is_list(self, client: TestClient) -> None:
        """Response data must be a list."""
        response = client.get("/api/v1/devices/test-fw-01/operations")
        body = response.json()
        assert isinstance(body["data"], list)


# ---------------------------------------------------------------------------
# POST /api/v1/devices/{name}/execute
# ---------------------------------------------------------------------------


class TestExecuteOperation:
    def test_returns_200(self, client: TestClient) -> None:
        """Execute endpoint must return HTTP 200."""
        response = client.post(
            "/api/v1/devices/test-fw-01/execute",
            params={"operation": "show_system_info"},
        )
        assert response.status_code == 200

    def test_response_status_is_ok(self, client: TestClient) -> None:
        """Response envelope must carry status='ok'."""
        response = client.post(
            "/api/v1/devices/test-fw-01/execute",
            params={"operation": "show_system_info"},
        )
        body = response.json()
        assert body["status"] == "ok"

    def test_operation_name_in_response(self, client: TestClient) -> None:
        """Response envelope must include the operation name from the query param."""
        response = client.post(
            "/api/v1/devices/test-fw-01/execute",
            params={"operation": "show_system_info"},
        )
        body = response.json()
        assert body["operation"] == "show_system_info"

    def test_device_name_in_response(self, client: TestClient) -> None:
        """Response envelope must include the device name from the path."""
        response = client.post(
            "/api/v1/devices/test-fw-01/execute",
            params={"operation": "show_system_info"},
        )
        body = response.json()
        assert body["device"] == "test-fw-01"
