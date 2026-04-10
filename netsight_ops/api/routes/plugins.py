"""Plugin management routes for NetSight API.

Provides an endpoint to list all registered plugins.  All installed packs
are discovered on first request via the ``netsight.packs`` entry-point group.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from netsight_ops.api.models.envelope import APIResponse
from netsight.registry import plugin_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])


def _ensure_panos_xml_registered() -> None:
    """Discover and load every installed pack via the entry-point group.

    Kept under the legacy name for call-site compatibility. Phase 6 of
    the install-packs refactor removed the panos-specific auto-register
    branch. A later release will rename this to ``_ensure_packs_loaded``.
    """
    try:
        from netsight.packs import pack_registry

        pack_registry.ensure_loaded()
    except Exception:
        logger.exception("Failed to load packs")


@router.get("")
def list_plugins() -> dict:
    """List all registered plugins.

    Auto-registers the panos_xml plugin if it is not already present,
    then returns a summary of every registered plugin.

    Returns:
        APIResponse envelope whose data is a list of plugin summary dicts,
        each containing the plugin ``name``, ``allowed_operations``, and
        any extra ``metadata``.
    """
    _ensure_panos_xml_registered()

    plugins = plugin_registry.list()
    plugin_data = [
        {
            "name": info.name,
            "allowed_operations": sorted(info.allowed_operations),
            "metadata": info.metadata,
        }
        for info in plugins
    ]

    return APIResponse.success(
        data=plugin_data,
        record_count=len(plugin_data),
    ).model_dump()
