"""Network-layer response models for NetSight API.

Covers routing table entries (RouteEntryResponse / ShowRoutesResponse),
interface inventory (InterfaceResponse), and ARP cache entries
(ArpEntryResponse).
"""

from __future__ import annotations

from pydantic import BaseModel


class RouteEntryResponse(BaseModel):
    """A single entry in the device routing table.

    Attributes:
        destination: Network destination prefix (e.g. ``"10.0.0.0/8"``).
        nexthop:     Next-hop IP address or interface name.
        interface:   Egress interface name.
        metric:      Route metric / administrative distance.
        flags:       Protocol / state flags string (e.g. ``"UG"``).
        age:         Route age in seconds, if available.
    """

    destination: str
    nexthop: str
    interface: str
    metric: int
    flags: str
    age: int | None = None


class ShowRoutesResponse(BaseModel):
    """Full routing table response.

    Attributes:
        total_routes: Number of routes in the table.
        routes:       Ordered list of route entries.
    """

    total_routes: int
    routes: list[RouteEntryResponse]


class InterfaceResponse(BaseModel):
    """Network interface summary.

    Attributes:
        name:   Interface name (e.g. ``"ethernet1/1"``).
        zone:   Security zone assigned to the interface.
        ip:     IP address (with prefix length if applicable).
        status: Operational status (e.g. ``"up"``, ``"down"``).
    """

    name: str
    zone: str = ""
    ip: str = ""
    status: str = ""


class ArpEntryResponse(BaseModel):
    """A single ARP cache entry.

    Attributes:
        interface: Interface on which the entry was learned.
        ip:        IP address of the neighbour.
        mac:       MAC address of the neighbour.
        status:    ARP entry state (e.g. ``"c"`` for complete).
        ttl:       Time-to-live in seconds before the entry expires.
    """

    interface: str
    ip: str
    mac: str
    status: str = ""
    ttl: int = 0
