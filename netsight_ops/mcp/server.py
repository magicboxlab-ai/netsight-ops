"""NetSight MCP Server — exposes live codebase introspection via MCP protocol.

Introspects the live codebase at runtime; no static documentation is used.
Tools, resources, and prompts are derived directly from registered plugins,
@operation-decorated methods, built-in patterns, and the relation graph.
"""

from __future__ import annotations

import logging
from typing import Any

from netsight.docs.export import export_full_catalog
from netsight.docs.patterns import get_builtin_patterns
from netsight.docs.relations import get_default_relation_graph
from netsight.registry import plugin_registry
import netsight.parsers  # noqa: F401 — registers types/transforms/engines
from netsight.parsers.registry import (
    parser_registry,
    transform_registry,
    type_registry,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Error guidance registry
# ---------------------------------------------------------------------------

_ERROR_GUIDANCE: dict[str, dict[str, str]] = {
    "CommandDeniedError": {
        "name": "CommandDeniedError",
        "description": (
            "Raised when a requested operation is blocked by the allow-list gate. "
            "Only operations in a plugin's allowed_operations set may be executed."
        ),
        "guidance": (
            "Check that the operation name is spelled correctly and matches an entry "
            "in the pack's compiled operations catalog (_data/operations_catalog.toml). "
            "Use list_tools() to see all permitted operations. If the operation is "
            "intentionally restricted, contact the administrator to update the "
            "allow-list."
        ),
    },
    "AuthenticationError": {
        "name": "AuthenticationError",
        "description": (
            "Raised when authentication against a device fails. "
            "Credentials are never included in exception messages to prevent exposure."
        ),
        "guidance": (
            "Verify that the username and password configured for the device are "
            "correct. Check that the device account has API access enabled. "
            "Confirm the device is reachable before re-attempting authentication. "
            "Rotate credentials if a compromise is suspected."
        ),
    },
    "DeviceConnectionError": {
        "name": "DeviceConnectionError",
        "description": (
            "Raised when a device is unreachable due to network failure, "
            "timeout, or DNS resolution issues."
        ),
        "guidance": (
            "Verify network connectivity to the device host. Check that the "
            "configured hostname or IP address is correct. Review firewall rules "
            "between the NetSight host and the device. Increase timeout_connect "
            "and timeout_read values in the device config for slow links."
        ),
    },
    "PluginNotFoundError": {
        "name": "PluginNotFoundError",
        "description": (
            "Raised when no plugin is registered for a requested api_type. "
            "Each device config must specify an api_type matching a registered plugin."
        ),
        "guidance": (
            "Ensure the plugin package is installed and imported before use. "
            "Call the plugin's register() function at application startup. "
            "Check the api_type field in your device configuration matches a "
            "registered plugin name exactly (case-sensitive). Use "
            "netsight://plugins to list all registered plugins."
        ),
    },
    "RateLimitError": {
        "name": "RateLimitError",
        "description": (
            "Raised when a device's request rate limit is exceeded. "
            "Each device config may specify a max requests-per-second value."
        ),
        "guidance": (
            "Reduce the frequency of requests to the device. Increase the "
            "rate_limit value in the device configuration if the device supports "
            "a higher throughput. Add delays between bulk operations. Consider "
            "batching multiple queries into a single operation where possible."
        ),
    },
    "ResponseSizeError": {
        "name": "ResponseSizeError",
        "description": (
            "Raised when a device response exceeds the configured size limit. "
            "Used to protect against unexpectedly large payloads."
        ),
        "guidance": (
            "Narrow your query by adding filters (e.g. nlogs, query parameters) "
            "to reduce the response size. Increase the max_response_bytes limit "
            "in the device configuration if larger responses are expected. "
            "Consider paginating large result sets across multiple calls."
        ),
    },
}


# ---------------------------------------------------------------------------
# NetSightMCPServer
# ---------------------------------------------------------------------------


class NetSightMCPServer:
    """MCP server that introspects the live NetSight codebase at runtime.

    On initialisation every installed pack is discovered via the
    ``netsight.packs`` entry-point group.  All tool, resource, and
    prompt data is derived from live registry state — not from static files.
    """

    def __init__(self) -> None:
        """Initialise the MCP server and discover installed packs."""
        self._ensure_panos_xml_registered()

    # ------------------------------------------------------------------
    # Auto-registration
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_panos_xml_registered() -> None:
        """Discover and load every installed pack via the entry-point group.

        Kept as a static method under the legacy name for backwards
        compatibility with the existing call sites in this file. Phase 6
        of the install-packs refactor deleted the panos-specific
        auto-register branch — the pack is now discovered like any other.
        A later release will rename this to ``_ensure_packs_loaded``.
        """
        from netsight.packs import pack_registry

        pack_registry.ensure_loaded()

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """Return all tool definitions from the live codebase.

        Combines tool definitions from export_full_catalog (sourced from
        @operation-decorated methods) with tools synthesised from each
        registered plugin's allowed_operations (excluding 'keygen').  The
        catalog definitions take precedence; plugin-derived tools are only
        added for operations not already present.

        Returns:
            List of tool definition dicts, each containing:
            - ``name``        — operation name
            - ``description`` — human-readable description
            - ``parameters``  — JSON Schema object
        """
        plugin_classes = [
            info.client_class for info in plugin_registry.list()
        ]

        catalog = export_full_catalog(plugin_classes)
        catalog_tools: list[dict[str, Any]] = catalog.get("tools", [])

        # Build a set of names already covered by the catalog
        catalog_names: set[str] = {t["name"] for t in catalog_tools}

        # Synthesise minimal tool stubs for allowed operations not in catalog
        extra_tools: list[dict[str, Any]] = []
        for plugin_info in plugin_registry.list():
            for op_name in sorted(plugin_info.allowed_operations):
                if op_name == "keygen":
                    continue
                if op_name not in catalog_names:
                    extra_tools.append(
                        {
                            "name": op_name,
                            "description": (
                                f"Execute {op_name} via the {plugin_info.name} plugin"
                            ),
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device": {
                                        "type": "string",
                                        "description": "Target device name",
                                    }
                                },
                                "required": ["device"],
                            },
                        }
                    )
                    catalog_names.add(op_name)

        tools = catalog_tools + extra_tools

        # Also read from compiled vendor configs
        try:
            from netsight.config_mgmt.store import FileConfigStore
            store = FileConfigStore("config/vendors")
            for vendor in store.list_vendors():
                for dt in store.list_models(vendor):
                    try:
                        resolved = store.get_resolved(vendor, dt)
                        for op_name, op_config in resolved.get("operations", {}).items():
                            if not any(t["name"] == op_name for t in tools):
                                tools.append({
                                    "name": op_name,
                                    "description": op_config.get("description", ""),
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "device": {"type": "string", "description": "Device name"},
                                        },
                                        "required": ["device"],
                                    },
                                    "category": op_config.get("category", ""),
                                    "vendor": vendor,
                                })
                    except FileNotFoundError:
                        continue
        except Exception:
            pass  # Fall back gracefully

        return tools

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    def list_resources(self) -> list[dict[str, Any]]:
        """Return all resource URIs exposed by this MCP server.

        Includes:
        - ``netsight://patterns``          — built-in usage patterns
        - ``netsight://relations``         — operation relation graph
        - ``netsight://plugins``           — registered plugin metadata
        - ``netsight://errors/{name}``     — error guidance for each known error

        Returns:
            List of resource dicts, each containing at minimum a ``uri`` key.
        """
        resources: list[dict[str, Any]] = [
            {
                "uri": "netsight://patterns",
                "description": "Built-in usage patterns — common investigation workflows",
            },
            {
                "uri": "netsight://relations",
                "description": "Operation relationship graph from the default PAN-OS graph",
            },
            {
                "uri": "netsight://plugins",
                "description": "Registered plugin metadata and allowed operations",
            },
            {
                "uri": "netsight://config",
                "name": "Compiled Configs",
                "description": "Compiled vendor configurations",
            },
        ]

        for error_name in _ERROR_GUIDANCE:
            resources.append(
                {
                    "uri": f"netsight://errors/{error_name}",
                    "description": _ERROR_GUIDANCE[error_name]["description"],
                }
            )

        resources.append({
            "uri": "netsight://engines",
            "name": "Parser Engines",
            "description": "Registered parser engines",
        })
        resources.append({
            "uri": "netsight://types",
            "name": "Field Types",
            "description": "Registered parser field types",
        })
        resources.append({
            "uri": "netsight://transforms",
            "name": "Transforms",
            "description": "Registered parser transforms",
        })

        return resources

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def list_prompts(self) -> list[dict[str, Any]]:
        """Return prompt definitions derived from the built-in patterns.

        Each pattern becomes a prompt with a mandatory ``device`` argument so
        AI agents know to supply a target device when invoking the prompt.

        Returns:
            List of prompt dicts, each containing:
            - ``name``        — pattern name
            - ``description`` — pattern description
            - ``arguments``   — list containing a required "device" argument
        """
        prompts: list[dict[str, Any]] = []
        for pattern in get_builtin_patterns():
            prompts.append(
                {
                    "name": pattern.name,
                    "description": pattern.description,
                    "arguments": [
                        {
                            "name": "device",
                            "description": "Target device name or identifier",
                            "required": True,
                        }
                    ],
                }
            )
        return prompts

    # ------------------------------------------------------------------
    # Resource content
    # ------------------------------------------------------------------

    def get_resource(self, uri: str) -> Any:
        """Return the content for a given resource URI.

        Args:
            uri: The resource URI to fetch.

        Returns:
            - For ``netsight://patterns``: list of pattern dicts with steps
            - For ``netsight://relations``: list of relation dicts
            - For ``netsight://plugins``: list of plugin info dicts
            - For ``netsight://errors/{name}``: error guidance dict
            - For unknown URIs: ``{"error": "Unknown resource: {uri}"}``
        """
        if uri == "netsight://patterns":
            return self._get_patterns()

        if uri == "netsight://relations":
            return self._get_relations()

        if uri == "netsight://plugins":
            return self._get_plugins()

        if uri == "netsight://engines":
            return parser_registry.list_names()
        if uri == "netsight://types":
            return type_registry.list_names()
        if uri == "netsight://transforms":
            return transform_registry.list_names()

        if uri == "netsight://config":
            try:
                from netsight.config_mgmt.store import FileConfigStore
                store = FileConfigStore("config/vendors")
                result = []
                for vendor in store.list_vendors():
                    for dt in store.list_models(vendor):
                        result.append({"vendor": vendor, "model": dt})
                return result
            except Exception:
                return []

        if uri.startswith("netsight://errors/"):
            error_name = uri[len("netsight://errors/"):]
            return self._get_error_guidance(error_name)

        logger.debug("MCP server: unknown resource URI requested: %s", uri)
        return {"error": f"Unknown resource: {uri}"}

    # ------------------------------------------------------------------
    # Private resource helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_patterns() -> list[dict[str, Any]]:
        """Return pattern list with steps from the live codebase."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "steps": [
                    {"operation": s.operation, "description": s.description}
                    for s in p.steps
                ],
            }
            for p in get_builtin_patterns()
        ]

    @staticmethod
    def _get_relations() -> list[dict[str, Any]]:
        """Return relation list from the default relation graph."""
        graph = get_default_relation_graph()
        return [
            {
                "source": r.source,
                "target": r.target,
                "type": r.relation_type,
            }
            for r in graph.all_relations()
        ]

    @staticmethod
    def _get_plugins() -> list[dict[str, Any]]:
        """Return plugin list with allowed operations and metadata."""
        result: list[dict[str, Any]] = []
        for info in plugin_registry.list():
            result.append(
                {
                    "name": info.name,
                    "operations": sorted(info.allowed_operations),
                    "metadata": info.metadata,
                }
            )
        return result

    @staticmethod
    def _get_error_guidance(error_name: str) -> dict[str, Any]:
        """Return guidance dict for a named error, or an error dict if unknown."""
        if error_name in _ERROR_GUIDANCE:
            return _ERROR_GUIDANCE[error_name]
        return {"error": f"Unknown error: {error_name}"}
