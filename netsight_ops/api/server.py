"""NetSight FastAPI application factory.

Call :func:`create_app` to obtain a fully configured :class:`fastapi.FastAPI`
instance with all routers mounted:

- REST routes under ``/api/v1`` (auth, devices, plugins, schema)
- GraphQL endpoint at ``/graphql`` (when strawberry is installed)
- WebSocket endpoints under ``/ws/v1/devices/``
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from netsight_ops.api.routes import (
    auth_router,
    devices_router,
    plugins_router,
    schema_router,
)
from netsight_ops.api.websocket.handlers import router as websocket_router

logger = logging.getLogger(__name__)

_API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    """Create and configure the NetSight FastAPI application.

    Registers CORS middleware and mounts REST, GraphQL (if available), and
    WebSocket routers.

    Returns:
        A :class:`FastAPI` instance with all available routers mounted.
    """
    app = FastAPI(
        title="NetSight API",
        description=(
            "NetSight REST API — network device introspection, "
            "operation execution, and schema export."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # REST routers
    # ------------------------------------------------------------------

    app.include_router(auth_router, prefix=_API_PREFIX)
    app.include_router(devices_router, prefix=_API_PREFIX)
    app.include_router(plugins_router, prefix=_API_PREFIX)
    app.include_router(schema_router, prefix=_API_PREFIX)

    # ------------------------------------------------------------------
    # GraphQL — optional; requires strawberry-graphql
    # ------------------------------------------------------------------

    try:
        from strawberry.fastapi import GraphQLRouter  # type: ignore[import-untyped]

        from netsight_ops.api.graphql.schema import schema as graphql_schema

        graphql_router = GraphQLRouter(graphql_schema)
        app.include_router(graphql_router, prefix="/graphql")
        logger.info("GraphQL router mounted at /graphql")
    except ImportError:
        logger.info("strawberry-graphql not available; GraphQL endpoint disabled")

    # ------------------------------------------------------------------
    # WebSocket handlers
    # ------------------------------------------------------------------

    app.include_router(websocket_router)

    logger.info("NetSight application created")
    return app
