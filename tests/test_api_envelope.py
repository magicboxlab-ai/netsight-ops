"""Tests for netsight_ops.api.models.envelope — APIResponse and ResponseMetadata."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from netsight_ops.api.models.envelope import APIResponse, ResponseMetadata


# ---------------------------------------------------------------------------
# ResponseMetadata
# ---------------------------------------------------------------------------


class TestResponseMetadata:
    def test_defaults(self) -> None:
        """Default metadata should have sensible zero values."""
        meta = ResponseMetadata()
        assert meta.format == "dict"
        assert meta.record_count is None
        assert meta.duration_ms == 0.0

    def test_request_id_is_valid_uuid(self) -> None:
        """Auto-generated request_id must be a valid UUID4 string."""
        meta = ResponseMetadata()
        # Should not raise
        parsed = uuid.UUID(meta.request_id)
        assert parsed.version == 4

    def test_request_ids_are_unique(self) -> None:
        """Each ResponseMetadata instance must have a unique request_id."""
        ids = {ResponseMetadata().request_id for _ in range(20)}
        assert len(ids) == 20

    def test_explicit_values(self) -> None:
        """Explicitly supplied values should be preserved exactly."""
        meta = ResponseMetadata(
            format="list",
            record_count=42,
            duration_ms=12.5,
            request_id="my-fixed-id",
        )
        assert meta.format == "list"
        assert meta.record_count == 42
        assert meta.duration_ms == 12.5
        assert meta.request_id == "my-fixed-id"


# ---------------------------------------------------------------------------
# APIResponse — success classmethod
# ---------------------------------------------------------------------------


class TestAPIResponseSuccess:
    def test_status_is_ok(self) -> None:
        resp = APIResponse.success(data={"key": "value"})
        assert resp.status == "ok"

    def test_data_is_preserved(self) -> None:
        payload = [1, 2, 3]
        resp = APIResponse.success(data=payload)
        assert resp.data == payload

    def test_optional_device(self) -> None:
        resp = APIResponse.success(data=None, device="fw-01")
        assert resp.device == "fw-01"

    def test_optional_operation(self) -> None:
        resp = APIResponse.success(data=None, operation="get_routes")
        assert resp.operation == "get_routes"

    def test_record_count_in_metadata(self) -> None:
        resp = APIResponse.success(data=[], record_count=5)
        assert resp.metadata.record_count == 5

    def test_duration_ms_in_metadata(self) -> None:
        resp = APIResponse.success(data=None, duration_ms=99.9)
        assert resp.metadata.duration_ms == pytest.approx(99.9)

    def test_defaults_device_and_operation_are_none(self) -> None:
        resp = APIResponse.success(data="x")
        assert resp.device is None
        assert resp.operation is None

    def test_timestamp_is_utc_aware(self) -> None:
        resp = APIResponse.success(data=None)
        assert resp.timestamp.tzinfo is not None
        assert resp.timestamp.utcoffset().total_seconds() == 0  # type: ignore[union-attr]

    def test_timestamp_is_recent(self) -> None:
        before = datetime.now(tz=timezone.utc)
        resp = APIResponse.success(data=None)
        after = datetime.now(tz=timezone.utc)
        assert before <= resp.timestamp <= after


# ---------------------------------------------------------------------------
# APIResponse — error classmethod
# ---------------------------------------------------------------------------


class TestAPIResponseError:
    def test_status_is_error(self) -> None:
        resp = APIResponse.error("something went wrong")
        assert resp.status == "error"

    def test_message_in_data(self) -> None:
        resp = APIResponse.error("device unreachable")
        assert isinstance(resp.data, dict)
        assert resp.data["message"] == "device unreachable"

    def test_optional_device(self) -> None:
        resp = APIResponse.error("fail", device="fw-02")
        assert resp.device == "fw-02"

    def test_optional_operation(self) -> None:
        resp = APIResponse.error("fail", operation="get_arp")
        assert resp.operation == "get_arp"

    def test_metadata_is_present(self) -> None:
        resp = APIResponse.error("fail")
        assert isinstance(resp.metadata, ResponseMetadata)

    def test_defaults_device_and_operation_are_none(self) -> None:
        resp = APIResponse.error("fail")
        assert resp.device is None
        assert resp.operation is None


# ---------------------------------------------------------------------------
# APIResponse — direct construction
# ---------------------------------------------------------------------------


class TestAPIResponseDirectConstruction:
    def test_custom_status(self) -> None:
        resp = APIResponse(status="pending", data=None)
        assert resp.status == "pending"

    def test_explicit_timestamp_preserved(self) -> None:
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        resp = APIResponse(status="ok", data=None, timestamp=ts)
        assert resp.timestamp == ts

    def test_metadata_default_factory(self) -> None:
        resp = APIResponse(status="ok", data=None)
        assert isinstance(resp.metadata, ResponseMetadata)

    def test_metadata_unique_per_instance(self) -> None:
        r1 = APIResponse(status="ok", data=None)
        r2 = APIResponse(status="ok", data=None)
        assert r1.metadata.request_id != r2.metadata.request_id
