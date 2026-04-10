"""MCP stdio transport — reads JSON-RPC messages from stdin, writes to stdout.

Implements the JSON-RPC 2.0 wire protocol for the MCP stdio transport.
Each line of stdin is treated as a complete JSON-RPC request object.
Responses are written as single JSON lines to stdout.

Supported methods:
- ``tools/list``      — delegates to NetSightMCPServer.list_tools()
- ``resources/list``  — delegates to NetSightMCPServer.list_resources()
- ``prompts/list``    — delegates to NetSightMCPServer.list_prompts()
- ``resources/read``  — delegates to NetSightMCPServer.get_resource(uri)
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from netsight_ops.mcp.server import NetSightMCPServer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------


def _make_result(request_id: Any, result: Any) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _make_error(
    request_id: Any,
    code: int,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error,
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def _dispatch(server: NetSightMCPServer, message: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a parsed JSON-RPC message to the appropriate server method.

    Args:
        server: The NetSightMCPServer instance to dispatch to.
        message: Parsed JSON-RPC request dict.

    Returns:
        A JSON-RPC response dict (success or error).
    """
    request_id = message.get("id")
    method = message.get("method", "")
    params = message.get("params") or {}

    try:
        if method == "tools/list":
            result = {"tools": server.list_tools()}
            return _make_result(request_id, result)

        if method == "resources/list":
            result = {"resources": server.list_resources()}
            return _make_result(request_id, result)

        if method == "prompts/list":
            result = {"prompts": server.list_prompts()}
            return _make_result(request_id, result)

        if method == "resources/read":
            uri = params.get("uri", "")
            content = server.get_resource(uri)
            result = {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content),
                    }
                ]
            }
            return _make_result(request_id, result)

        # Method not found
        logger.debug("MCP transport: unknown method '%s'", method)
        return _make_error(
            request_id,
            code=-32601,
            message=f"Method not found: {method}",
        )

    except Exception as exc:  # pragma: no cover
        logger.exception("MCP transport: internal error handling method '%s': %s", method, exc)
        return _make_error(
            request_id,
            code=-32603,
            message="Internal error",
            data=str(exc),
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_stdio() -> None:
    """Read JSON-RPC messages from stdin and write responses to stdout.

    Each input line is expected to be a complete JSON-RPC 2.0 request.
    Each output line is a complete JSON-RPC 2.0 response.

    Lines that are empty or cannot be parsed as JSON are silently skipped.
    The loop exits when stdin reaches EOF.
    """
    server = NetSightMCPServer()
    logger.info("MCP stdio transport started")

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.debug("MCP transport: could not parse line as JSON: %s", exc)
            # Write a parse error response with null id (per JSON-RPC spec)
            response = _make_error(None, code=-32700, message="Parse error")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = _dispatch(server, message)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    logger.info("MCP stdio transport: stdin closed, exiting")
