"""Log-related response models for NetSight API.

Covers individual log entries returned by traffic / security log queries.
"""

from __future__ import annotations

from pydantic import BaseModel


class LogEntryResponse(BaseModel):
    """A single security or traffic log entry.

    Attributes:
        time_generated:  Timestamp string from the device log.
        src:             Source IP address.
        dst:             Destination IP address.
        app:             Application identifier.
        action:          Policy action (e.g. ``"allow"``, ``"deny"``).
        rule:            Name of the matching security rule.
        bytes_sent:      Bytes sent from source to destination.
        bytes_received:  Bytes received from destination to source.
    """

    time_generated: str = ""
    src: str = ""
    dst: str = ""
    app: str = ""
    action: str = ""
    rule: str = ""
    bytes_sent: int = 0
    bytes_received: int = 0
