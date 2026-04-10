"""Strawberry GraphQL type definitions for NetSight.

Exposes plugin, pattern, and relation data as queryable GraphQL types.
"""

from __future__ import annotations

import strawberry


@strawberry.type
class PluginType:
    """A registered NetSight device plugin."""

    name: str
    description: str
    operations: list[str]


@strawberry.type
class PatternStepType:
    """A single step in a usage pattern."""

    operation: str
    description: str


@strawberry.type
class PatternType:
    """A documented workflow pattern composed of ordered steps."""

    name: str
    description: str
    steps: list[PatternStepType]


@strawberry.type
class RelationType:
    """A relationship between two operations."""

    source: str
    target: str
    relation_type: str
