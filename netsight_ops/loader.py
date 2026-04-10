"""Entry-point discovery for netsight-ops services."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netsight_ops.registry import ServiceRegistry

logger = logging.getLogger(__name__)


def load_installed_services(registry: ServiceRegistry) -> None:
    """Discover and load all ``netsight_ops.services`` entry points.

    Each entry point's callable receives *registry* and is expected
    to call ``registry.register(ServiceInfo(...))``. Failures are
    isolated per service.
    """
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    import netsight
    import netsight_ops
    from netsight_ops.exceptions import ServiceIncompatibleError

    eps = entry_points(group="netsight_ops.services")
    for ep in eps:
        try:
            register_fn = ep.load()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Service %r failed to import: %s", ep.name, exc)
            registry.record_load_error(ep.name, exc)
            continue

        try:
            register_fn(registry)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Service %r register() raised: %s", ep.name, exc)
            registry.record_load_error(ep.name, exc)
            continue

        if not registry.has(ep.name):
            continue

        info = registry.get(ep.name)

        # Check 1 — service API version.
        if info.declared_service_api != netsight_ops.SERVICE_API_VERSION:
            registry.unregister(ep.name)
            registry.record_load_error(
                ep.name,
                ServiceIncompatibleError(
                    service_name=ep.name,
                    detail=(
                        f"declared_service_api={info.declared_service_api} "
                        f"does not match SERVICE_API_VERSION="
                        f"{netsight_ops.SERVICE_API_VERSION}"
                    ),
                ),
            )
            continue

        # Check 2 — ops version range.
        if info.min_ops_version:
            try:
                spec = SpecifierSet(info.min_ops_version)
                if Version(netsight_ops.__version__) not in spec:
                    registry.unregister(ep.name)
                    registry.record_load_error(
                        ep.name,
                        ServiceIncompatibleError(
                            service_name=ep.name,
                            detail=(
                                f"netsight-ops {netsight_ops.__version__!r} "
                                f"does not satisfy {info.min_ops_version!r}"
                            ),
                        ),
                    )
                    continue
            except Exception as exc:  # noqa: BLE001
                registry.unregister(ep.name)
                registry.record_load_error(ep.name, exc)
                continue

        # Check 3 — SDK version range.
        if info.min_sdk_version:
            try:
                spec = SpecifierSet(info.min_sdk_version)
                if Version(netsight.__version__) not in spec:
                    registry.unregister(ep.name)
                    registry.record_load_error(
                        ep.name,
                        ServiceIncompatibleError(
                            service_name=ep.name,
                            detail=(
                                f"netsight-sdk {netsight.__version__!r} "
                                f"does not satisfy {info.min_sdk_version!r}"
                            ),
                        ),
                    )
                    continue
            except Exception as exc:  # noqa: BLE001
                registry.unregister(ep.name)
                registry.record_load_error(ep.name, exc)
                continue
