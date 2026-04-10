"""GraphQL resolver functions for NetSight queries.

Each resolver maps a domain object to the corresponding Strawberry type,
auto-registering built-in plugins on first call when necessary.
"""

from __future__ import annotations

import logging

from netsight.docs.patterns import get_builtin_patterns
from netsight.docs.relations import get_default_relation_graph
from netsight.registry import plugin_registry

from .types import PatternStepType, PatternType, PluginType, RelationType

logger = logging.getLogger(__name__)


def resolve_plugins() -> list[PluginType]:
    """Return all registered plugins as GraphQL types.

    Ensures all installed packs are loaded via the entry-point group so
    that the query always returns results for every installed pack in a
    default deployment.

    Returns:
        List of PluginType objects for every registered plugin.
    """
    try:
        from netsight.packs import pack_registry  # noqa: PLC0415

        pack_registry.ensure_loaded()
    except Exception:
        logger.warning("Could not load packs", exc_info=True)

    result: list[PluginType] = []
    for info in plugin_registry.list():
        description: str = info.metadata.get("description", "")
        result.append(
            PluginType(
                name=info.name,
                description=description,
                operations=sorted(info.allowed_operations),
            )
        )
    return result


def resolve_patterns() -> list[PatternType]:
    """Return all built-in usage patterns as GraphQL types.

    Returns:
        List of PatternType objects from get_builtin_patterns().
    """
    result: list[PatternType] = []
    for pattern in get_builtin_patterns():
        steps = [
            PatternStepType(operation=step.operation, description=step.description)
            for step in pattern.steps
        ]
        result.append(
            PatternType(
                name=pattern.name,
                description=pattern.description,
                steps=steps,
            )
        )
    return result


def resolve_relations() -> list[RelationType]:
    """Return all operation relations from the default relation graph as GraphQL types.

    Returns:
        List of RelationType objects from get_default_relation_graph().
    """
    graph = get_default_relation_graph()
    return [
        RelationType(
            source=rel.source,
            target=rel.target,
            relation_type=rel.relation_type,
        )
        for rel in graph.all_relations()
    ]
