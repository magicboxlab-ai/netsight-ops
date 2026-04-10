"""API response models for NetSight.

Exports the APIResponse envelope and ResponseMetadata, plus all typed response
models for system, network, and log operations.
"""

from __future__ import annotations

from netsight_ops.api.models.envelope import APIResponse, ResponseMetadata
from netsight_ops.api.models.responses.logs import LogEntryResponse
from netsight_ops.api.models.responses.network import (
    ArpEntryResponse,
    InterfaceResponse,
    RouteEntryResponse,
    ShowRoutesResponse,
)
from netsight_ops.api.models.responses.system import HAStatusResponse, SystemInfoResponse

__all__ = [
    "APIResponse",
    "ResponseMetadata",
    "SystemInfoResponse",
    "HAStatusResponse",
    "RouteEntryResponse",
    "ShowRoutesResponse",
    "InterfaceResponse",
    "ArpEntryResponse",
    "LogEntryResponse",
]
