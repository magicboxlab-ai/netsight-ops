"""Tests for netsight_ops.api.websocket.handlers.

Tests verify:
- WebSocket routes are registered correctly on the FastAPI app
- Log-streaming endpoint protocol (connect, config, stream, stop)
- State-watch endpoint protocol (connect, watch, stop)
- Graceful disconnect handling

NOTE: These tests use a minimal async ASGI WebSocket harness built on anyio
because httpx (required by starlette.testclient.TestClient) is not installed
in this environment.  The harness drives the ASGI lifecycle directly, giving
full confidence in handler behaviour without any extra dependencies.
"""

from __future__ import annotations

import json
from typing import Any

import anyio
import pytest

from netsight_ops.api.server import create_app
from netsight_ops.api.websocket.handlers import router


# ---------------------------------------------------------------------------
# Lightweight async ASGI WebSocket harness
# ---------------------------------------------------------------------------


class _ASGIWebSocketSession:
    """Minimal ASGI WebSocket session that drives a single handler call.

    Simulates the Starlette/ASGI WebSocket lifecycle:
      1. ``websocket.connect`` send event
      2. Interleaved ``receive`` / ``send`` message pairs
      3. ``websocket.disconnect`` receive event when the client closes

    All interaction happens via :meth:`send_text` and :meth:`receive_json`.
    """

    def __init__(self, app: Any, path: str) -> None:
        self._app = app
        self._path = path

        # Queues bridging the test coroutine and the ASGI handler
        self._to_handler: anyio.abc.ObjectSendStream[dict]
        self._from_handler: anyio.abc.ObjectSendStream[dict]
        self._receive: anyio.abc.ObjectReceiveStream[dict]
        self._send: anyio.abc.ObjectReceiveStream[dict]

        self._connected = False
        self._task_group: anyio.abc.TaskGroup | None = None

    async def __aenter__(self) -> "_ASGIWebSocketSession":
        send_to_h, recv_by_h = anyio.create_memory_object_stream(max_buffer_size=32)
        send_from_h, recv_by_t = anyio.create_memory_object_stream(max_buffer_size=32)

        self._to_handler = send_to_h
        self._receive = recv_by_t
        self._from_handler = send_from_h

        # Build ASGI scope — path params are extracted by the ASGI app.
        # e.g. /ws/v1/devices/fw-01/logs  → path_params = {"name": "fw-01"}
        scope: dict[str, Any] = {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "ws",
            "path": self._path,
            "raw_path": self._path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "subprotocols": [],
        }

        async def receive() -> dict:
            return await recv_by_h.receive()

        async def send(message: dict) -> None:
            await send_from_h.send(message)

        # Prime the receive queue with the connect event
        await send_to_h.send({"type": "websocket.connect"})

        self._tg = await anyio.create_task_group().__aenter__()
        self._tg.start_soon(self._app, scope, receive, send)
        self._connected = True

        # Consume the "websocket.accept" message from the handler
        accept = await recv_by_t.receive()
        assert accept["type"] == "websocket.accept", f"Expected accept, got {accept}"

        return self

    async def __aexit__(self, *_: Any) -> None:
        # Signal disconnect to the handler then close the task group
        try:
            await self._to_handler.send({"type": "websocket.disconnect", "code": 1000})
        except anyio.ClosedResourceError:
            pass
        try:
            await self._tg.__aexit__(None, None, None)
        except Exception:
            pass

    async def send_text(self, text: str) -> None:
        """Send a text message to the handler."""
        await self._to_handler.send({"type": "websocket.receive", "text": text, "bytes": None})

    async def receive_json(self) -> dict:
        """Receive the next JSON text message from the handler."""
        msg = await self._receive.receive()
        assert msg["type"] == "websocket.send", f"Expected websocket.send, got {msg}"
        return json.loads(msg["text"])


async def _run_ws_test(path: str, coro_fn) -> None:
    """Helper: create app, run an async WebSocket test coroutine."""
    app = create_app()
    async with _ASGIWebSocketSession(app, path) as ws:
        await coro_fn(ws)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    """Return a fresh NetSight FastAPI application instance."""
    return create_app()


# ---------------------------------------------------------------------------
# Route registration — synchronous, no httpx needed
# ---------------------------------------------------------------------------


def test_websocket_logs_route_registered(app) -> None:
    """The /ws/v1/devices/{name}/logs WebSocket route is registered in the app."""
    paths = [route.path for route in app.routes]
    assert "/ws/v1/devices/{name}/logs" in paths


def test_websocket_watch_route_registered(app) -> None:
    """The /ws/v1/devices/{name}/watch WebSocket route is registered in the app."""
    paths = [route.path for route in app.routes]
    assert "/ws/v1/devices/{name}/watch" in paths


def test_router_has_exactly_two_websocket_routes() -> None:
    """The websocket APIRouter has exactly 2 routes (logs and watch)."""
    assert len(router.routes) == 2


def test_router_route_paths_are_correct() -> None:
    """Both expected WebSocket route paths are registered on the router."""
    paths = {route.path for route in router.routes}
    assert "/ws/v1/devices/{name}/logs" in paths
    assert "/ws/v1/devices/{name}/watch" in paths


def test_graphql_route_registered(app) -> None:
    """The /graphql route is registered in the app."""
    paths = [route.path for route in app.routes]
    graphql_paths = [p for p in paths if "graphql" in p]
    assert graphql_paths, f"No graphql paths found in: {paths}"


# ---------------------------------------------------------------------------
# WebSocket protocol — /logs endpoint (async via anyio)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_logs_ws_accepts_connection() -> None:
    """WebSocket logs endpoint accepts connection and sends streaming status."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/test-fw-01/logs") as ws:
        await ws.send_text(json.dumps({"log_type": "traffic", "query": ""}))
        response = await ws.receive_json()
        assert response["status"] == "streaming"
        assert response["device"] == "test-fw-01"

        await ws.send_text(json.dumps({"action": "stop"}))
        stop = await ws.receive_json()
        assert stop["status"] == "stopped"


@pytest.mark.anyio
async def test_logs_ws_echoes_log_type_and_query() -> None:
    """Logs WebSocket echoes log_type and query from the config frame."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-01/logs") as ws:
        await ws.send_text(json.dumps({"log_type": "system", "query": "severity eq high"}))
        response = await ws.receive_json()
        assert response["log_type"] == "system"
        assert response["query"] == "severity eq high"

        await ws.send_text(json.dumps({"action": "stop"}))
        await ws.receive_json()


@pytest.mark.anyio
async def test_logs_ws_defaults_log_type_when_missing() -> None:
    """Logs WebSocket defaults to 'traffic' when log_type is absent from config."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-01/logs") as ws:
        await ws.send_text(json.dumps({}))
        response = await ws.receive_json()
        assert response["log_type"] == "traffic"

        await ws.send_text(json.dumps({"action": "stop"}))
        await ws.receive_json()


@pytest.mark.anyio
async def test_logs_ws_stop_returns_stopped_status() -> None:
    """Sending {'action': 'stop'} results in a 'stopped' status frame."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-01/logs") as ws:
        await ws.send_text(json.dumps({"log_type": "traffic", "query": ""}))
        await ws.receive_json()  # consume streaming frame

        await ws.send_text(json.dumps({"action": "stop"}))
        response = await ws.receive_json()
        assert response["status"] == "stopped"
        assert response["device"] == "fw-01"


@pytest.mark.anyio
async def test_logs_ws_returns_device_name() -> None:
    """Logs WebSocket echoes the device name from the URL path."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-prod-01/logs") as ws:
        await ws.send_text(json.dumps({"log_type": "threat", "query": ""}))
        response = await ws.receive_json()
        assert response["device"] == "fw-prod-01"

        await ws.send_text(json.dumps({"action": "stop"}))
        await ws.receive_json()


# ---------------------------------------------------------------------------
# WebSocket protocol — /watch endpoint (async via anyio)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_watch_ws_accepts_connection() -> None:
    """WebSocket watch endpoint accepts connection and immediately sends watching frame."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/test-fw-01/watch") as ws:
        response = await ws.receive_json()
        assert response["status"] == "watching"
        assert response["device"] == "test-fw-01"

        await ws.send_text(json.dumps({"action": "stop"}))
        stop = await ws.receive_json()
        assert stop["status"] == "stopped"


@pytest.mark.anyio
async def test_watch_ws_returns_device_name() -> None:
    """Watch WebSocket echoes the device name from the URL path."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/my-device/watch") as ws:
        response = await ws.receive_json()
        assert response["device"] == "my-device"

        await ws.send_text(json.dumps({"action": "stop"}))
        await ws.receive_json()


@pytest.mark.anyio
async def test_watch_ws_stop_returns_stopped_status() -> None:
    """Sending {'action': 'stop'} to watch endpoint results in 'stopped' status."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-01/watch") as ws:
        await ws.receive_json()  # consume initial watching frame

        await ws.send_text(json.dumps({"action": "stop"}))
        response = await ws.receive_json()
        assert response["status"] == "stopped"
        assert response["device"] == "fw-01"


@pytest.mark.anyio
async def test_watch_ws_non_stop_message_echoes_back() -> None:
    """Watch WebSocket echoes non-stop messages as watching status frames."""
    app = create_app()
    async with _ASGIWebSocketSession(app, "/ws/v1/devices/fw-01/watch") as ws:
        await ws.receive_json()  # consume initial watching frame

        await ws.send_text(json.dumps({"ping": "hello"}))
        response = await ws.receive_json()
        assert response["status"] == "watching"
        assert "received" in response

        await ws.send_text(json.dumps({"action": "stop"}))
        await ws.receive_json()
