"""Service protocol, registry, and supporting types for netsight-ops."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from netsight_ops.exceptions import ServiceConflictError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service protocol + base class
# ---------------------------------------------------------------------------


@runtime_checkable
class Service(Protocol):
    """Contract every netsight-ops service implements.

    Services are long-running processes wrapping the NetSight SDK.
    They expose some kind of communication channel (HTTP, stdio,
    WebSocket, gRPC, etc.) and are discovered via the
    ``netsight_ops.services`` entry-point group at startup.
    """

    @property
    def name(self) -> str: ...

    def start(self, *, config: "ServiceConfig") -> None:
        """Begin listening. Must be idempotent if called while running."""
        ...

    def stop(self) -> None:
        """Release resources. Must be idempotent."""
        ...

    def health(self) -> dict:
        """Return a shallow status dict for readiness probes."""
        ...


class ServiceBase:
    """Optional convenience base class with sensible defaults.

    Authors who want the sugar inherit from ``ServiceBase`` and
    override ``start()`` / ``stop()`` / ``health()``. Authors who
    prefer pure structural typing implement ``Service`` directly.
    """

    _name: str = ""
    _running: bool = False

    @property
    def name(self) -> str:
        return self._name or type(self).__name__

    def start(self, *, config: "ServiceConfig") -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def health(self) -> dict:
        return {"name": self.name, "running": self._running}


# ---------------------------------------------------------------------------
# ServiceInfo + ServiceConfig
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceInfo:
    """Metadata record for a single registered netsight-ops service.

    Attributes
    ----------
    name:
        Canonical service name (e.g. ``"api"``, ``"mcp"``).
    display_name:
        Human-friendly name for CLI output.
    description:
        One-line summary.
    version:
        Installed distribution version.
    distribution:
        PyPI distribution name that ships this service.
    factory:
        Callable that returns a ``Service`` instance.
    cli_verb:
        Subcommand name for ``netsight-ops serve <verb>``.
    transport:
        Communication protocol hint: ``"tcp"``, ``"stdio"``, etc.
    min_ops_version:
        PEP 440 specifier for the minimum netsight-ops version.
    min_sdk_version:
        PEP 440 specifier for the minimum netsight-sdk version.
    declared_service_api:
        Must match ``SERVICE_API_VERSION`` at load time.
    """

    name: str
    display_name: str
    description: str
    version: str
    distribution: str
    factory: Callable[[], Service]
    cli_verb: str | None = None
    transport: str = "tcp"
    min_ops_version: str = ""
    min_sdk_version: str = ""
    declared_service_api: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConfig:
    """Runtime configuration passed to ``Service.start()``."""

    host: str = "0.0.0.0"
    port: int = 8000
    transport: str = "tcp"
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ServiceRegistry
# ---------------------------------------------------------------------------


class ServiceRegistry:
    """Central registry of installed netsight-ops services.

    Mirrors the shape of ``netsight.packs.registry.PackRegistry``:
    register, get, list, ensure_loaded, record_load_error.
    """

    def __init__(self) -> None:
        self._services: dict[str, ServiceInfo] = {}
        self._errors: dict[str, Exception] = {}
        self._loaded: bool = False

    def register(self, info: ServiceInfo) -> None:
        if info.name in self._services:
            raise ServiceConflictError(info.name)
        self._services[info.name] = info
        logger.info("Service registered: '%s' v%s", info.name, info.version)

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)

    def get(self, name: str) -> ServiceInfo:
        try:
            return self._services[name]
        except KeyError:
            raise KeyError(
                f"Service '{name}' is not registered. "
                "Check service name or call ensure_loaded() first."
            ) from None

    def has(self, name: str) -> bool:
        return name in self._services

    def list(self) -> list[ServiceInfo]:
        return list(self._services.values())

    def record_load_error(self, name: str, exc: Exception) -> None:
        self._errors[name] = exc
        logger.warning("Service '%s' failed to load: %s: %s", name, type(exc).__name__, exc)

    def load_errors(self) -> dict[str, Exception]:
        return dict(self._errors)

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        from netsight_ops.loader import load_installed_services
        load_installed_services(self)
        self._loaded = True


service_registry: ServiceRegistry = ServiceRegistry()
