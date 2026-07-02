from __future__ import annotations

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES
from foi_o_nz.extractors import build_message_events, iter_message_records
from foi_o_nz.normalise import build_request_profile, normalise_records

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
