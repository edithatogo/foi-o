from __future__ import annotations

from foi_o_nz.transitions import audit_transitions


def test_transition_audit_flags_unexpected_transition() -> None:
    events = [
        {
            "event_id": "foio-nz:event:1",
            "event_time": "2026-01-01T00:00:00Z",
            "request_ref": {"source_request_id": "r1"},
            "lifecycle_state_after": "Received",
        },
        {
            "event_id": "foio-nz:event:2",
            "event_time": "2026-01-02T00:00:00Z",
            "request_ref": {"source_request_id": "r1"},
            "lifecycle_state_after": "Refused",
        },
    ]
    result = audit_transitions(events)
    assert not result["ok"]
    assert result["finding_count"] == 1


def test_transition_audit_accepts_known_transition() -> None:
    events = [
        {
            "event_id": "foio-nz:event:1",
            "event_time": "2026-01-01T00:00:00Z",
            "request_ref": {"source_request_id": "r1"},
            "lifecycle_state_after": "Received",
        },
        {
            "event_id": "foio-nz:event:2",
            "event_time": "2026-01-02T00:00:00Z",
            "request_ref": {"source_request_id": "r1"},
            "lifecycle_state_after": "SearchPlanning",
        },
    ]
    result = audit_transitions(events)
    assert result["ok"]
