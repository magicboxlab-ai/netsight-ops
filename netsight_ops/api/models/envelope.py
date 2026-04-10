"""Standard API response envelope for NetSight.

All API endpoints return an APIResponse wrapping their payload.  The envelope
carries a ``status`` discriminator (``"ok"`` / ``"error"``), optional device
and operation context, a UTC timestamp, and a ResponseMetadata block that
exposes pagination / timing / tracing information.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Metadata attached to every API response."""

    format: str = "dict"
    record_count: int | None = None
    duration_ms: float = 0.0
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class APIResponse(BaseModel):
    """Standardised envelope returned by all NetSight API endpoints.

    Attributes:
        status:     ``"ok"`` for successful responses, ``"error"`` for failures.
        device:     Name of the target device, if applicable.
        operation:  The operation that was performed, if applicable.
        timestamp:  UTC time the response was created.
        data:       The response payload — any JSON-serialisable value.
        metadata:   Timing, record count, and request-ID information.
    """

    status: str
    device: str | None = None
    operation: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    data: Any = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)

    @classmethod
    def success(
        cls,
        data: Any,
        device: str | None = None,
        operation: str | None = None,
        record_count: int | None = None,
        duration_ms: float = 0.0,
    ) -> "APIResponse":
        """Build a successful response envelope.

        Args:
            data:         The payload to include in the response.
            device:       Optional device name for context.
            operation:    Optional operation name for context.
            record_count: Number of records in ``data``, if applicable.
            duration_ms:  Time taken to produce the response in milliseconds.

        Returns:
            An :class:`APIResponse` with ``status="ok"``.
        """
        return cls(
            status="ok",
            device=device,
            operation=operation,
            data=data,
            metadata=ResponseMetadata(
                record_count=record_count,
                duration_ms=duration_ms,
            ),
        )

    @classmethod
    def error(
        cls,
        message: str,
        device: str | None = None,
        operation: str | None = None,
    ) -> "APIResponse":
        """Build an error response envelope.

        Args:
            message:   Human-readable error description placed in ``data``.
            device:    Optional device name for context.
            operation: Optional operation name for context.

        Returns:
            An :class:`APIResponse` with ``status="error"``.
        """
        return cls(
            status="error",
            device=device,
            operation=operation,
            data={"message": message},
            metadata=ResponseMetadata(),
        )
