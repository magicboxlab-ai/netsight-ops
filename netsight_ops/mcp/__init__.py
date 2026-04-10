"""NetSight runtime MCP operations server.

Exposes live device operations — ``show_system_info``, ``get_traffic_logs``,
etc. — to AI agents via the MCP stdio transport. This is the **runtime**
MCP server for querying actual devices, distinct from the **dev** MCP server
(``netsight.mcp_dev``) that introspects the codebase for development tooling.

As a netsight-ops built-in service, it registers itself via the
``netsight_ops.services`` entry-point group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netsight_ops.registry import ServiceRegistry

from netsight_ops.mcp.server import NetSightMCPServer
from netsight_ops.mcp.transport import run_stdio


class MCPOpsService:
    """Built-in runtime MCP service implementing the ``Service`` protocol."""

    _name = "mcp"
    _running = False
    _server: NetSightMCPServer | None = None

    @property
    def name(self) -> str:
        return self._name

    def start(self, *, config=None) -> None:
        self._running = True
        run_stdio()  # blocks on stdin
        self._running = False

    def stop(self) -> None:
        self._running = False

    def health(self) -> dict:
        return {"name": self.name, "running": self._running}


def create_mcp_server() -> NetSightMCPServer:
    """Return a configured MCP server instance for programmatic use."""
    return NetSightMCPServer()


def register(registry: "ServiceRegistry") -> None:
    """Entry point — called by netsight_ops.loader at startup."""
    from netsight_ops.registry import ServiceInfo

    registry.register(ServiceInfo(
        name="mcp",
        display_name="Runtime MCP Server",
        description="MCP stdio server exposing live device operations to AI agents",
        version="0.1.0",
        distribution="netsight-ops",
        factory=MCPOpsService,
        cli_verb="mcp",
        transport="stdio",
    ))


__all__ = ["NetSightMCPServer", "MCPOpsService", "create_mcp_server", "run_stdio", "register"]
