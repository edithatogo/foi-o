"""Lifecycle transition auditing over event streams."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from foi_o_nz.io import iter_jsonl
from foi_o_nz.state_machine import RequestState, can_transition


def _state(value: object) -> RequestState | None:
    if value is None:
        return None
    try:
        return RequestState(str(value))
    except ValueError:
        return RequestState.UNKNOWN


def _request_key(event: dict[str, Any]) -> str:
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict):
        return str(
            request_ref.get("source_request_id") or request_ref.get("url_title") or "unknown"
        )
    return "unknown"


def audit_transitions(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit lifecycle_state_after sequences for each request."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[_request_key(event)].append(event)
    findings: list[dict[str, Any]] = []
    transition_count = 0
    for request_id, request_events in grouped.items():
        request_events.sort(key=lambda item: str(item.get("event_time") or ""))
        previous: RequestState | None = None
        previous_event_id: str | None = None
        for event in request_events:
            current = _state(event.get("lifecycle_state_after"))
            if current is None:
                continue
            if previous is not None and current != previous:
                transition_count += 1
                if not can_transition(previous, current):
                    findings.append(
                        {
                            "severity": "warning",
                            "code": "unexpected_transition",
                            "request_id": request_id,
                            "from_state": previous.value,
                            "to_state": current.value,
                            "previous_event_id": previous_event_id,
                            "event_id": event.get("event_id"),
                            "message": "transition is not in the conservative process profile",
                        }
                    )
            previous = current
            previous_event_id = str(event.get("event_id") or "") or None
    return {
        "ok": not findings,
        "request_count": len(grouped),
        "transition_count": transition_count,
        "finding_count": len(findings),
        "findings": findings,
    }


def audit_transitions_jsonl(path: Path) -> dict[str, Any]:
    """Audit transitions from an events JSONL file."""
    return audit_transitions(list(iter_jsonl(path)))
