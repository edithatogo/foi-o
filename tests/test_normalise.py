from __future__ import annotations

import json
from pathlib import Path

import pytest

from foi_o_nz.normalise import (
    build_observed_events,
    build_request_profile,
    normalise_manifest_file,
    normalise_records,
)

RECORD = {
    "request_id": 123,
    "url_title": "123_test_request",
    "title": "Test request",
    "authority": "Test Ministry",
    "state": "partially_successful",
    "first_sent": "2026-06-01T00:00:00Z",
    "last_updated": "2026-06-03T00:00:00Z",
    "content_sha256": "b" * 64,
    "html_captured": True,
    "attachments": [],
    "warc_record_ids": ["warc:1"],
}


def test_build_request_profile_maps_state_and_clock() -> None:
    profile = build_request_profile(RECORD)

    assert profile.normalised_state == "ReleasedInPart"
    assert profile.state_mapping is not None
    assert profile.state_mapping.method == "rule"
    assert profile.legal_clock is not None
    assert profile.legal_clock.decision_due_date is not None
    assert profile.source_provenance is not None
    assert profile.source_provenance.source_record_id == "123"
    assert profile.source_provenance.raw_state_field == "state"
    assert profile.source_provenance.raw_state_value == "partially_successful"
    assert profile.source_provenance.mapping_method == "rule"
    assert profile.source_provenance.mapping_confidence == 0.58
    assert profile.source_provenance.evidence_id == "evidence:fyi-archive-nz:123:manifest"


def test_build_observed_events() -> None:
    profile = build_request_profile(RECORD)
    events = build_observed_events(profile)

    assert [event.event_type for event in events] == [
        "RequestObserved",
        "StateObserved",
        "DeadlineCalculated",
    ]
    assert events[1].payload["source_state"] == "partially_successful"


def test_normalise_manifest_file_jsonl(tmp_path: Path) -> None:
    input_path = tmp_path / "manifest.jsonl"
    input_path.write_text(json.dumps(RECORD) + "\n", encoding="utf-8")
    requests_output = tmp_path / "requests.jsonl"
    events_output = tmp_path / "events.jsonl"
    run_manifest = tmp_path / "run-manifest.json"

    manifest = normalise_manifest_file(
        input_path,
        requests_output=requests_output,
        events_output=events_output,
        run_manifest_output=run_manifest,
    )

    assert manifest["request_count"] == 1
    assert manifest["event_count"] == 3
    assert requests_output.exists()
    assert events_output.exists()
    assert run_manifest.exists()


@pytest.mark.parametrize(
    ("payload", "filename"),
    [
        ([RECORD], "manifest-array.json"),
        ({"records": [RECORD]}, "manifest-records-wrapper.json"),
    ],
)
def test_normalise_manifest_file_json_variants_include_source_provenance(
    tmp_path: Path, payload: object, filename: str
) -> None:
    input_path = tmp_path / filename
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    requests_output = tmp_path / "requests.jsonl"
    events_output = tmp_path / "events.jsonl"

    manifest = normalise_manifest_file(
        input_path,
        requests_output=requests_output,
        events_output=events_output,
    )

    assert manifest["request_count"] == 1
    request = json.loads(requests_output.read_text(encoding="utf-8").splitlines()[0])
    assert request["source_state"] == "partially_successful"
    assert request["normalised_state"] == "ReleasedInPart"
    assert request["source_provenance"] == {
        "input_path": str(input_path),
        "source_record_id": "123",
        "raw_state_field": "state",
        "raw_state_value": "partially_successful",
        "mapping_method": "rule",
        "mapping_confidence": 0.58,
        "evidence_id": "evidence:fyi-archive-nz:123:manifest",
    }


def test_live_source_configuration_fails_closed_before_outputs(tmp_path: Path) -> None:
    missing_input = tmp_path / "missing-live-manifest.jsonl"
    requests_output = tmp_path / "requests.jsonl"
    events_output = tmp_path / "events.jsonl"

    with pytest.raises(RuntimeError, match="external gate"):
        normalise_manifest_file(
            missing_input,
            requests_output=requests_output,
            events_output=events_output,
            live_source_url="https://huggingface.co/datasets/edithatogo/fyi-archive-nz",
        )

    assert not requests_output.exists()
    assert not events_output.exists()


def test_normalise_records_extracts_message_events() -> None:
    record = {
        **RECORD,
        "messages": [
            {
                "id": "m1",
                "date": "2026-06-10T00:00:00Z",
                "body": "We need to extend the time limit for your request by 10 working days.",
            }
        ],
    }
    _profiles, events = normalise_records([record])
    event_types = [event.event_type for event in events]

    assert "MessageObserved" in event_types
    assert "ExtensionNotified" in event_types
    extension_event = next(event for event in events if event.event_type == "ExtensionNotified")
    assert extension_event.requires_human_certification
    assert extension_event.human_certification is not None
    assert extension_event.human_certification.certified is False
    assert extension_event.legal_references[0].reference == "s 15A"
