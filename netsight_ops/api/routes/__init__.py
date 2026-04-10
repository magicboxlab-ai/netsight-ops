"""NetSight API route modules.

Each sub-module exposes a :class:`fastapi.APIRouter` instance under the
name ``router``.  Import these routers in :func:`netsight_ops.api.server.create_app`
and include them under the ``/api/v1`` prefix.
"""

from netsight_ops.api.routes.auth import router as auth_router
from netsight_ops.api.routes.devices import router as devices_router
from netsight_ops.api.routes.plugins import router as plugins_router
from netsight_ops.api.routes.schema import router as schema_router

__all__ = [
    "auth_router",
    "devices_router",
    "plugins_router",
    "schema_router",
]
