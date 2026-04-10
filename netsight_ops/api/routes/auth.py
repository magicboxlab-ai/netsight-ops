"""Authentication stub routes for NetSight API.

Provides placeholder login and token endpoints.  These stubs return
informational messages and are intended as scaffolding for a full
authentication implementation.
"""

from __future__ import annotations

from fastapi import APIRouter

from netsight_ops.api.models.envelope import APIResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login() -> dict:
    """Stub login endpoint — returns an informational message.

    Returns:
        APIResponse envelope with a message indicating the endpoint is a stub.
    """
    return APIResponse.success(
        data={"message": "Login endpoint — not yet implemented"}
    ).model_dump()


@router.post("/token")
def token() -> dict:
    """Stub token endpoint — returns an informational message.

    Returns:
        APIResponse envelope with a message indicating the endpoint is a stub.
    """
    return APIResponse.success(
        data={"message": "Token endpoint — not yet implemented"}
    ).model_dump()
