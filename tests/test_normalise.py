from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.normalise import build_observed_events, build_request_profile, normalise_manifest_file


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


def test_build_request_profile_maps_state() -> None:
    profile = build_request_profile(RECORD)

    assert profile.normalised_state == "ReleasedInPart"
    assert profile.state_mapping is not None
    assert profile.state_mapping.method == "rule"


def test_build_observed_events() -> None:
    profile = build_request_profile(RECORD)
    events = build_observed_events(profile)

    assert [event.event_type for event in events] == ["RequestObserved", "StateObserved"]
    assert events[1].payload["source_state"] == "partially_successful"


def test_normalise_manifest_file_jsonl(tmp_path: Path) -> None:
    input_path = tmp_path / "manifest.jsonl"
    input_path.write_text(json.dumps(RECORD) + "\n", encoding="utf-8")
    requests_output = tmp_path / "requests.jsonl"
    events_output = tmp_path / "events.jsonl"

    manifest = normalise_manifest_file(
        input_path,
        requests_output=requests_output,
        events_output=events_output,
    )

    assert manifest["request_count"] == 1
    assert manifest["event_count"] == 2
    assert requests_output.exists()
    assert events_output.exists()
