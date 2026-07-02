from __future__ import annotations

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.extractors import build_message_events, iter_message_records
from foi_o_nz.normalise import build_request_profile, normalise_records
from foi_o_nz.timeline import build_event_timeline

BASE_RECORD = {
    "request_id": "evt-1",
    "url_title": "evt_1_test_request",
    "title": "Event extraction test request",
    "authority": "Example Ministry",
    "state": "waiting_response",
    "first_sent": "2026-06-01T00:00:00Z",
    "last_updated": "2026-06-02T00:00:00Z",
    "content_sha256": "c" * 64,
}


def test_iter_message_records_covers_supported_manifest_shapes() -> None:
    record = {
        **BASE_RECORD,
        "correspondence": ["We need to extend the time limit."],
        "messages": [{"id": "m1", "body": "Please clarify the scope."}],
        "communications": {"id": "m2", "text": "We are transferring the request."},
        "updates": [{"message_id": "m3", "content": "An invoice charge may apply."}],
        "mail": [{"id": "m4", "html_to_text": "You may complain to the Ombudsman."}],
        "description": "We have made a decision.",
    }

    messages = iter_message_records(record)

    assert [message.message_id for message in messages] == [
        "correspondence:0",
        "m1",
        "m2",
        "m3",
        "m4",
        "description:0",
    ]
    assert all(message.body for message in messages)


def test_candidate_event_rules_and_certification_boundary() -> None:
    profile = build_request_profile(BASE_RECORD)
    messages = iter_message_records(
        {
            **BASE_RECORD,
            "messages": [
                {"id": "extension", "body": "We extend the time limit by 10 working days."},
                {"id": "transfer", "body": "We are transferring this under section 14."},
                {"id": "clarify", "body": "Please clarify the scope of your request."},
                {"id": "charge", "body": "A charge, deposit, or invoice may apply."},
                {"id": "refusal", "body": "We refuse this under section 18."},
                {"id": "release", "body": "The requested documents are attached and provided."},
                {"id": "complaint", "body": "You may complain to the Ombudsman."},
                {"id": "decision", "body": "This is our decision on your request."},
            ],
        }
    )

    events = build_message_events(profile, messages)
    by_type = {event.event_type: event for event in events}

    for event_type in [
        "ExtensionNotified",
        "TransferNotified",
        "ClarificationRequested",
        "ChargeNoticeSent",
        "RefusalCommunicated",
        "ReleaseMade",
        "ComplaintObserved",
        "DecisionCommunicated",
    ]:
        assert event_type in by_type
        assert by_type[event_type].assertion_status == "inferred"
        assert by_type[event_type].confidence is not None
        assert by_type[event_type].evidence[0].evidence_type == "message"
        assert "requires_human_review" in by_type[event_type].quality_flags

    for event_type, event in by_type.items():
        if event_type in HUMAN_CERTIFICATION_EVENT_TYPES:
            assert event.requires_human_certification
            assert event.human_certification is not None
            assert event.human_certification.certified is False

    assert by_type["ClarificationRequested"].requires_human_certification is False
    assert by_type["ComplaintObserved"].requires_human_certification is False


def test_normalise_records_keeps_message_observation_and_candidates() -> None:
    _profiles, events = normalise_records(
        [
            {
                **BASE_RECORD,
                "messages": [{"id": "release", "body": "The documents are attached."}],
            }
        ]
    )

    event_types = [event.event_type for event in events]
    assert "MessageObserved" in event_types
    assert "ReleaseMade" in event_types


def test_timeline_orders_by_time_source_order_and_event_id() -> None:
    timeline = build_event_timeline(
        [
            {
                "event_id": "foio-nz:event:late",
                "event_type": "ReleaseMade",
                "event_time": "2026-06-03T00:00:00Z",
                "request_ref": {"source_request_id": "evt-1"},
                "lifecycle_state_after": "ReleasedInPart",
                "assertion_status": "inferred",
                "confidence": 0.38,
                "evidence": [{"evidence_id": "evidence:late"}],
            },
            {
                "event_id": "foio-nz:event:early-b",
                "event_type": "MessageObserved",
                "event_time": "2026-06-01T00:00:00Z",
                "request_ref": {"source_request_id": "evt-1"},
                "assertion_status": "observed",
                "confidence": 1.0,
                "evidence": [{"evidence_id": "evidence:early-b"}],
            },
            {
                "event_id": "foio-nz:event:early-a",
                "event_type": "RequestObserved",
                "event_time": "2026-06-01T00:00:00Z",
                "request_ref": {"source_request_id": "evt-1"},
                "payload": {"source_state": "waiting_response"},
                "assertion_status": "observed",
                "confidence": 1.0,
                "evidence": [{"evidence_id": "evidence:early-a"}],
            },
        ]
    )

    assert [event["event_id"] for event in timeline["events"]] == [
        "foio-nz:event:early-b",
        "foio-nz:event:early-a",
        "foio-nz:event:late",
    ]
    assert timeline["events"][1]["source_state"] == "waiting_response"
    assert timeline["events"][2]["evidence_ids"] == ["evidence:late"]


def test_timeline_missing_and_invalid_dates_warn_without_fabricated_precision() -> None:
    timeline = build_event_timeline(
        [
            {
                "event_id": "foio-nz:event:missing",
                "event_type": "MessageObserved",
                "request_ref": {"source_request_id": "evt-1"},
                "evidence": [{"evidence_id": "evidence:missing"}],
            },
            {
                "event_id": "foio-nz:event:invalid",
                "event_type": "MessageObserved",
                "event_time": "not-a-date",
                "request_ref": {"source_request_id": "evt-1"},
                "evidence": [{"evidence_id": "evidence:invalid"}],
            },
        ]
    )

    assert [event["event_time"] for event in timeline["events"]] == [None, None]
    assert timeline["warning_count"] == 2
    assert [warning["code"] for warning in timeline["warnings"]] == [
        "missing_event_time",
        "invalid_event_time",
    ]
