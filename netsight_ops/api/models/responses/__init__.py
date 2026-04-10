"""Typed Pydantic response models for NetSight API endpoints.

Grouped by domain:
- ``system``:  SystemInfoResponse, HAStatusResponse
- ``network``: RouteEntryResponse, ShowRoutesResponse, InterfaceResponse, ArpEntryResponse
- ``logs``:    LogEntryResponse
"""

from __future__ import annotations

from netsight_ops.api.models.responses.logs import LogEntryResponse
from netsight_ops.api.models.responses.network import (
    ArpEntryResponse,
    InterfaceResponse,
    RouteEntryResponse,
    ShowRoutesResponse,
)
from netsight_ops.api.models.responses.system import HAStatusResponse, SystemInfoResponse

__all__ = [
    "SystemInfoResponse",
    "HAStatusResponse",
    "RouteEntryResponse",
    "ShowRoutesResponse",
    "InterfaceResponse",
    "ArpEntryResponse",
    "LogEntryResponse",
]
