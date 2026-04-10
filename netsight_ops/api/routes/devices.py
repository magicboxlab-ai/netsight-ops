"""Device management routes for NetSight API.

Provides stub endpoints for listing devices and executing operations
against named devices.  These stubs return informational responses and
are intended as scaffolding for a full device-integration implementation.
"""

from __future__ import annotations

from fastapi import APIRouter

from netsight_ops.api.models.envelope import APIResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("")
def list_devices() -> dict:
    """List all configured devices.

    Stub implementation — returns an empty list.  A full implementation
    would load the device list from the application configuration store.

    Returns:
        APIResponse envelope whose data is an empty list.
    """
    return APIResponse.success(
        data=[],
        record_count=0,
    ).model_dump()


@router.get("/{name}/info")
def device_info(name: str) -> dict:
    """Return configuration and status information for a named device.

    Stub implementation — returns a placeholder info dict.

    Args:
        name: The device name as it appears in the configuration.

    Returns:
        APIResponse envelope with basic device info stub data.
    """
    return APIResponse.success(
        data={"message": f"Device info for '{name}' — not yet implemented"},
        device=name,
    ).model_dump()


@router.get("/{name}/operations")
def list_operations(name: str) -> dict:
    """List the operations available for a named device.

    Stub implementation — returns an empty list.  A full implementation
    would look up the device's plugin from the registry and return its
    ``allowed_operations``.

    Args:
        name: The device name as it appears in the configuration.

    Returns:
        APIResponse envelope whose data is an empty list.
    """
    return APIResponse.success(
        data=[],
        device=name,
        record_count=0,
    ).model_dump()


@router.post("/{name}/execute")
def execute_operation(name: str, operation: str) -> dict:
    """Execute a named operation against a device.

    Stub implementation — acknowledges the request without performing any
    real device communication.

    Args:
        name: The device name as it appears in the configuration.
        operation: The operation to execute (supplied as a query parameter).

    Returns:
        APIResponse envelope with a stub acknowledgement message.
    """
    return APIResponse.success(
        data={"message": f"Execute '{operation}' on '{name}' — not yet implemented"},
        device=name,
        operation=operation,
    ).model_dump()
