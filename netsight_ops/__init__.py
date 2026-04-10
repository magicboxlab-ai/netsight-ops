"""netsight-ops — Runtime service platform for NetSight.

Provides the ``Service`` protocol, ``ServiceRegistry``, and built-in
services (HTTP API + runtime MCP) that wrap the netsight-sdk core
library for production deployments.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__: str = _pkg_version("netsight-ops")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

SERVICE_API_VERSION: int = 1

from netsight_ops.registry import (  # noqa: E402
    Service,
    ServiceBase,
    ServiceConfig,
    ServiceInfo,
    ServiceRegistry,
    service_registry,
)

__all__ = [
    "__version__",
    "SERVICE_API_VERSION",
    "Service",
    "ServiceBase",
    "ServiceConfig",
    "ServiceInfo",
    "ServiceRegistry",
    "service_registry",
]
