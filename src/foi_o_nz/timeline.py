"""Deterministic event timeline reconstruction helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foi_o_nz.dates import parse_datetime
from foi_o_nz.io import iter_jsonl, write_json


def _request_id(event: dict[str, Any]) -> str | None:
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict):
        value = request_ref.get("source_request_id") or request_ref.get("url_title")
        return str(value) if value is not None else None
    value = event.get("request_id")
    return str(value) if value is not None else None


def _evidence_ids(event: dict[str, Any]) -> list[str]:
    evidence = event.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [
        str(item.get("evidence_id"))
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id") is not None
    ]


def _source_state(event: dict[str, Any]) -> str | None:
    payload = event.get("payload")
    if isinstance(payload, dict) and payload.get("source_state") is not None:
        return str(payload["source_state"])
    return None


def _timeline_item(
    event: dict[str, Any], *, source_index: int, parsed_time: datetime | None
) -> dict[str, Any]:
    return {
        "source_index": source_index,
        "event_id": event.get("event_id"),
        "request_id": _request_id(event),
        "event_type": event.get("event_type"),
        "event_time": parsed_time.isoformat() if parsed_time is not None else None,
        "source_state": _source_state(event),
        "lifecycle_state_after": event.get("lifecycle_state_after"),
        "assertion_status": event.get("assertion_status"),
        "confidence": event.get("confidence"),
        "evidence_ids": _evidence_ids(event),
        "quality_flags": event.get("quality_flags", []),
    }


def build_event_timeline(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a deterministic event timeline without fabricating missing precision."""
    warnings: list[dict[str, Any]] = []
    sortable: list[tuple[tuple[bool, datetime, int, str], dict[str, Any]]] = []
    for source_index, event in enumerate(events):
        raw_time = event.get("event_time")
        parsed_time = parse_datetime(raw_time)
        event_id = str(event.get("event_id") or f"source-index:{source_index}")
        if raw_time in {None, ""}:
            warnings.append(
                {
                    "code": "missing_event_time",
                    "event_id": event_id,
                    "message": "event_time missing; timeline order falls back to source order",
                }
            )
        elif parsed_time is None:
            warnings.append(
                {
                    "code": "invalid_event_time",
                    "event_id": event_id,
                    "raw_event_time": raw_time,
                    "message": "event_time could not be parsed; timeline order falls back to source order",
                }
            )
        sort_time = parsed_time or datetime.max.replace(tzinfo=UTC)
        sortable.append(
            (
                (parsed_time is None, sort_time, source_index, event_id),
                _timeline_item(event, source_index=source_index, parsed_time=parsed_time),
            )
        )
    ordered = [item for _key, item in sorted(sortable, key=lambda pair: pair[0])]
    return {
        "schema_version": "foi-o-nz.event-timeline.v0.1.0",
        "event_count": len(ordered),
        "warning_count": len(warnings),
        "warnings": warnings,
        "events": ordered,
        "limitations": [
            "Timeline order is deterministic process reconstruction only; missing or invalid times are not fabricated."
        ],
    }


def write_event_timeline(events_jsonl: Path, output: Path) -> dict[str, Any]:
    """Write a deterministic event timeline from an event JSONL stream."""
    timeline = build_event_timeline(list(iter_jsonl(events_jsonl)))
    write_json(output, timeline)
    return timeline
