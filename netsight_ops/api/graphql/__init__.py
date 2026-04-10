"""NetSight GraphQL interface.

Exposes the compiled Strawberry schema and query resolvers for use by
the FastAPI GraphQL router.
"""

from __future__ import annotations

from .schema import Query, schema

__all__ = ["Query", "schema"]
