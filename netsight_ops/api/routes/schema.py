"""Schema introspection routes for NetSight API.

Provides an endpoint that returns auto-generated tool definitions built
from all operation classes registered via the @operation decorator.
"""

from __future__ import annotations

from fastapi import APIRouter

from netsight_ops.api.models.envelope import APIResponse
from netsight.docs.export import export_full_catalog

router = APIRouter(prefix="/schema", tags=["schema"])

# Operation classes whose @operation-decorated methods are included in the
# auto-generated catalog.  Add new classes here as plugins are onboarded.
_OPERATION_CLASSES: list[type] = []


@router.get("/operations")
def operations_schema() -> dict:
    """Return the auto-generated tool definitions catalog.

    Calls :func:`~netsight.docs.export.export_full_catalog` to introspect
    all registered operation classes and combines the resulting tool
    definitions with built-in usage patterns and the default relation graph.

    Returns:
        APIResponse envelope whose data is the full operations catalog dict,
        containing ``"tools"``, ``"patterns"``, and ``"relations"`` keys.
    """
    catalog = export_full_catalog(operation_classes=_OPERATION_CLASSES)
    return APIResponse.success(
        data=catalog,
        record_count=len(catalog.get("tools", [])),
    ).model_dump()
