"""Developer utilities for netsight-ops service authors.

This module provides validation and scaffolding helpers for people
writing new services that plug into the ``netsight_ops.services``
entry-point group. It mirrors the role that ``netsight.mcp_dev``
plays for pack authors in the SDK — but scoped to the ops service
contract.

Available utilities:

- :func:`validate_service_class` — verify a class satisfies the
  ``Service`` protocol at the structural level.
- :func:`validate_service_entry_point` — check a pyproject.toml
  declares the entry point correctly.
- :func:`list_registered_services` — convenience wrapper around
  ``service_registry.ensure_loaded()`` + ``list()``.
"""

from __future__ import annotations

import inspect
from typing import Any

from netsight_ops.registry import Service, ServiceConfig, service_registry


def validate_service_class(cls: type) -> list[str]:
    """Return a list of protocol violations for *cls*.

    An empty list means *cls* satisfies the ``Service`` protocol.
    Each entry is a human-readable string describing one violation.
    """
    issues: list[str] = []

    # Check name property
    if not isinstance(inspect.getattr_static(cls, "name", None), (property, str)):
        if "name" not in cls.__dict__ and "_name" not in cls.__dict__:
            issues.append("Missing 'name' property or '_name' class attribute")

    # Check required methods
    for method_name in ("start", "stop", "health"):
        method = getattr(cls, method_name, None)
        if method is None or not callable(method):
            issues.append(f"Missing callable '{method_name}' method")

    # Check start() accepts keyword config
    start = getattr(cls, "start", None)
    if start is not None and callable(start):
        sig = inspect.signature(start)
        params = list(sig.parameters.keys())
        if "config" not in params and len(params) < 2:
            issues.append("start() should accept a 'config' keyword argument")

    # Check health() returns dict
    # (can't check without instantiating, so just check signature)
    health = getattr(cls, "health", None)
    if health is not None and callable(health):
        sig = inspect.signature(health)
        if len(sig.parameters) > 1:  # just self
            issues.append("health() should take no arguments besides self")

    return issues


def validate_service_entry_point(pyproject_path: str) -> list[str]:
    """Validate that a pyproject.toml declares the service entry point.

    Returns a list of issues. Empty means valid.
    """
    import tomllib
    from pathlib import Path

    path = Path(pyproject_path)
    if not path.is_file():
        return [f"File not found: {pyproject_path}"]

    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        return [f"TOML parse error: {exc}"]

    eps = data.get("project", {}).get("entry-points", {})
    services_group = eps.get("netsight_ops.services", {})

    if not services_group:
        return [
            'No [project.entry-points."netsight_ops.services"] section found. '
            "Services must declare their entry point in this group."
        ]

    issues: list[str] = []
    for name, value in services_group.items():
        if ":" not in value:
            issues.append(
                f"Entry point '{name} = {value!r}' is missing a ':' separator. "
                f"Expected format: 'module.path:register_function'"
            )

    return issues


def list_registered_services() -> list[dict[str, Any]]:
    """Return metadata for every registered service.

    Calls ``service_registry.ensure_loaded()`` first so entry-point
    discovery runs if it hasn't already.
    """
    service_registry.ensure_loaded()
    return [
        {
            "name": info.name,
            "display_name": info.display_name,
            "description": info.description,
            "version": info.version,
            "transport": info.transport,
            "distribution": info.distribution,
        }
        for info in service_registry.list()
    ]
