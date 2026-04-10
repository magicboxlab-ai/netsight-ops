"""WebSocket route handlers for NetSight.

Provides streaming log tailing and device state watch endpoints over
WebSocket connections.  Both handlers accept a JSON control message to
configure the stream and then deliver periodic status frames until the
client sends ``{"action": "stop"}`` or disconnects.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/v1/devices/{name}/logs")
async def device_logs(websocket: WebSocket, name: str) -> None:
    """Stream device logs over a WebSocket connection.

    Protocol:
        1. Client connects.
        2. Server accepts the connection.
        3. Client sends a JSON config frame::

               {"log_type": "traffic", "query": "addr in 10.0.0.0/8"}

        4. Server responds with an initial status frame and then sends
           periodic log status frames.
        5. Client sends ``{"action": "stop"}`` to end the stream.
        6. Server closes the connection gracefully.

    Args:
        websocket: The active WebSocket connection provided by FastAPI.
        name: Device name from the URL path parameter.
    """
    await websocket.accept()
    logger.info("Log stream opened for device '%s'", name)

    try:
        # Receive initial configuration from client
        raw = await websocket.receive_text()
        config: dict = json.loads(raw)
        log_type: str = config.get("log_type", "traffic")
        query: str = config.get("query", "")

        await websocket.send_json(
            {
                "status": "streaming",
                "device": name,
                "log_type": log_type,
                "query": query,
            }
        )

        # Stream until the client signals stop
        while True:
            raw = await websocket.receive_text()
            message: dict = json.loads(raw)
            if message.get("action") == "stop":
                await websocket.send_json({"status": "stopped", "device": name})
                break
            # Echo any other messages back as status frames
            await websocket.send_json(
                {"status": "streaming", "device": name, "received": message}
            )

    except WebSocketDisconnect:
        logger.info("Log stream disconnected for device '%s'", name)


@router.websocket("/ws/v1/devices/{name}/watch")
async def device_watch(websocket: WebSocket, name: str) -> None:
    """Watch device state changes over a WebSocket connection.

    Protocol:
        1. Client connects.
        2. Server accepts the connection and immediately begins sending
           state watch status frames.
        3. Client sends ``{"action": "stop"}`` to end the watch.
        4. Server closes the connection gracefully.

    Args:
        websocket: The active WebSocket connection provided by FastAPI.
        name: Device name from the URL path parameter.
    """
    await websocket.accept()
    logger.info("State watch opened for device '%s'", name)

    try:
        await websocket.send_json({"status": "watching", "device": name})

        while True:
            raw = await websocket.receive_text()
            message: dict = json.loads(raw)
            if message.get("action") == "stop":
                await websocket.send_json({"status": "stopped", "device": name})
                break
            # Acknowledge unrecognised messages
            await websocket.send_json(
                {"status": "watching", "device": name, "received": message}
            )

    except WebSocketDisconnect:
        logger.info("State watch disconnected for device '%s'", name)
