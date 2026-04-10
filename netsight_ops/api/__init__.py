"""NetSight HTTP API service — FastAPI + GraphQL + auth backends.

This package provides the HTTP API surface for NetSight, including
Pydantic response models, auth backends (API key, JWT, OAuth),
FastAPI routes, WebSocket handlers, and a GraphQL schema.

As a netsight-ops built-in service, it registers itself via the
``netsight_ops.services`` entry-point group and is auto-discovered
at startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netsight_ops.registry import ServiceRegistry


def create_fastapi_app():
    """Return a configured FastAPI application instance.

    This is the library entry point for embedding the NetSight HTTP
    API inside a larger application::

        from netsight_ops.api import create_fastapi_app
        app = create_fastapi_app()
        # mount at /netsight or run directly with uvicorn
    """
    from netsight_ops.api.server import create_app
    return create_app()


class HTTPAPIService:
    """Built-in HTTP API service implementing the ``Service`` protocol."""

    _name = "api"
    _running = False

    @property
    def name(self) -> str:
        return self._name

    def start(self, *, config=None) -> None:
        import uvicorn
        from netsight_ops.api.server import create_app

        cfg = config or {}
        app = create_app()
        host = getattr(cfg, "host", None) or cfg.get("host", "0.0.0.0") if isinstance(cfg, dict) else getattr(cfg, "host", "0.0.0.0")
        port = getattr(cfg, "port", None) or cfg.get("port", 8000) if isinstance(cfg, dict) else getattr(cfg, "port", 8000)
        self._running = True
        uvicorn.run(app, host=host, port=port)
        self._running = False

    def stop(self) -> None:
        self._running = False

    def health(self) -> dict:
        return {"name": self.name, "running": self._running}


def register(registry: "ServiceRegistry") -> None:
    """Entry point — called by netsight_ops.loader at startup."""
    from netsight_ops.registry import ServiceInfo

    registry.register(ServiceInfo(
        name="api",
        display_name="HTTP API Server",
        description="FastAPI + GraphQL REST surface with JWT/OAuth/APIKey auth",
        version="0.1.0",
        distribution="netsight-ops",
        factory=HTTPAPIService,
        cli_verb="api",
        transport="tcp",
    ))


__all__ = ["create_fastapi_app", "HTTPAPIService", "register"]
