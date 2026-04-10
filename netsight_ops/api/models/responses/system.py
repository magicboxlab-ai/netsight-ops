"""System-level response models for NetSight API.

Covers device identity (SystemInfoResponse) and high-availability state
(HAStatusResponse).
"""

from __future__ import annotations

from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    """Device system information.

    Attributes:
        hostname:   The device hostname.
        ip_address: Management IP address.
        model:      Hardware / software model string.
        serial:     Device serial number.
        sw_version: Running software / OS version.
        uptime:     Human-readable uptime string.
    """

    hostname: str
    ip_address: str
    model: str
    serial: str
    sw_version: str
    uptime: str


class HAStatusResponse(BaseModel):
    """High-availability pair status.

    Attributes:
        enabled:     Whether HA is configured and active.
        local_state: HA state of the local unit (e.g. ``"active"``, ``"passive"``).
        peer_state:  HA state of the peer unit.
        local_ip:    Management IP of the local unit.
        peer_ip:     Management IP of the peer unit.
    """

    enabled: bool
    local_state: str
    peer_state: str
    local_ip: str = ""
    peer_ip: str = ""
