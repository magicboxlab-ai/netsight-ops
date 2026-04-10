"""Testing utilities for netsight-ops service authors."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from netsight_ops.registry import Service, ServiceConfig, ServiceRegistry


def make_test_registry() -> ServiceRegistry:
    """Return a fresh, empty ServiceRegistry for testing."""
    return ServiceRegistry()


def assert_valid_service(service_or_cls: Any) -> None:
    """Assert *service_or_cls* satisfies the ``Service`` protocol."""
    if isinstance(service_or_cls, type):
        obj = service_or_cls()
    else:
        obj = service_or_cls
    assert isinstance(obj, Service), (
        f"{type(obj).__name__} does not satisfy the Service protocol"
    )
    assert hasattr(obj, "name"), "Service must have a 'name' property"
    assert callable(getattr(obj, "start", None)), "Service must have a start() method"
    assert callable(getattr(obj, "stop", None)), "Service must have a stop() method"
    assert callable(getattr(obj, "health", None)), "Service must have a health() method"


@contextmanager
def run_service_briefly(svc: Service, config: ServiceConfig | None = None):
    """Context manager: start/stop a service, yield it while 'running'."""
    cfg = config or ServiceConfig()
    try:
        svc.start(config=cfg)
        yield svc
    finally:
        svc.stop()
