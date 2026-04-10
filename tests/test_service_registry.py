"""Tests for the netsight-ops ServiceRegistry."""

from __future__ import annotations

import pytest

from netsight_ops.exceptions import ServiceConflictError
from netsight_ops.registry import (
    ServiceBase,
    ServiceConfig,
    ServiceInfo,
    ServiceRegistry,
    Service,
)


def _make_info(name: str = "test-svc", **overrides) -> ServiceInfo:
    defaults = dict(
        name=name,
        display_name="Test Service",
        description="A test service",
        version="0.1.0",
        distribution="netsight-ops-test",
        factory=ServiceBase,
        cli_verb=name,
        transport="tcp",
    )
    defaults.update(overrides)
    return ServiceInfo(**defaults)


class TestServiceRegistry:
    def test_register_and_get(self) -> None:
        reg = ServiceRegistry()
        info = _make_info()
        reg.register(info)
        assert reg.has("test-svc")
        assert reg.get("test-svc") is info

    def test_duplicate_raises_conflict(self) -> None:
        reg = ServiceRegistry()
        reg.register(_make_info())
        with pytest.raises(ServiceConflictError):
            reg.register(_make_info())

    def test_unregister(self) -> None:
        reg = ServiceRegistry()
        reg.register(_make_info())
        reg.unregister("test-svc")
        assert not reg.has("test-svc")

    def test_unregister_nonexistent_is_noop(self) -> None:
        reg = ServiceRegistry()
        reg.unregister("nonexistent")  # no error

    def test_list_returns_all(self) -> None:
        reg = ServiceRegistry()
        reg.register(_make_info("alpha"))
        reg.register(_make_info("beta"))
        names = {s.name for s in reg.list()}
        assert names == {"alpha", "beta"}

    def test_get_unknown_raises_key_error(self) -> None:
        reg = ServiceRegistry()
        with pytest.raises(KeyError):
            reg.get("nope")

    def test_record_load_error(self) -> None:
        reg = ServiceRegistry()
        exc = RuntimeError("boom")
        reg.record_load_error("broken", exc)
        assert "broken" in reg.load_errors()
        assert reg.load_errors()["broken"] is exc


class TestServiceProtocol:
    def test_service_base_satisfies_protocol(self) -> None:
        svc = ServiceBase()
        assert isinstance(svc, Service)

    def test_service_base_name_default(self) -> None:
        svc = ServiceBase()
        assert svc.name == "ServiceBase"

    def test_service_base_start_stop(self) -> None:
        svc = ServiceBase()
        svc.start(config=ServiceConfig())
        assert svc.health()["running"] is True
        svc.stop()
        assert svc.health()["running"] is False


class TestServiceInfo:
    def test_defaults(self) -> None:
        info = _make_info()
        assert info.declared_service_api == 1
        assert info.min_ops_version == ""
        assert info.min_sdk_version == ""
        assert info.transport == "tcp"

    def test_frozen(self) -> None:
        info = _make_info()
        with pytest.raises(AttributeError):
            info.name = "changed"  # type: ignore[misc]
