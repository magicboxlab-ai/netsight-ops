"""Strawberry GraphQL schema for NetSight.

Assembles the Query root type and exports the compiled schema object.
"""

from __future__ import annotations

import strawberry

from .queries import resolve_patterns, resolve_plugins, resolve_relations
from .types import PatternType, PluginType, RelationType


@strawberry.type
class Query:
    """Root GraphQL query type."""

    plugins: list[PluginType] = strawberry.field(resolver=resolve_plugins)
    patterns: list[PatternType] = strawberry.field(resolver=resolve_patterns)
    relations: list[RelationType] = strawberry.field(resolver=resolve_relations)


schema = strawberry.Schema(query=Query)
