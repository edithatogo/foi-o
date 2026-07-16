"""Tests for the reconciled NZ source-pack human review boundary."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
READINESS = ROOT / "examples/v2/nz-source-pack-review-readiness.2026-07-16.json"
SCHEMA = ROOT / "schemas/json/nz-source-pack-review-readiness.schema.json"
APPROVAL = ROOT / "examples/v2/human-promotion-review-packet.approved.json"


def test_source_pack_readiness_is_schema_valid_and_fail_closed() -> None:
    result = validate_json_schema(READINESS, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(READINESS.read_text())
    assert payload["source_pack_ready"] is False
    assert payload["source_pack_promotion_allowed"] is False
    assert payload["event_time_intervals"]["interval_count"] == 0
    assert payload["non_legislation_sources"]["artifact_count"] == 0


def test_prior_named_human_approvals_are_exactly_hash_pinned() -> None:
    payload = json.loads(READINESS.read_text())
    approval = json.loads(APPROVAL.read_text())
    assert payload["approved_review_packet_sha256"] == sha256(APPROVAL.read_bytes()).hexdigest()
    assert payload["reviewer"] == approval["reviewer"]
    approved = {item["artifact_path"]: item for item in approval["items"]}
    for component in payload["approved_components"]:
        path = ROOT / component["artifact_path"]
        item = approved[component["artifact_path"]]
        assert item["decision"] == "approved"
        assert item["artifact_sha256"] == component["artifact_sha256"]
        assert component["artifact_sha256"] == sha256(path.read_bytes()).hexdigest()


def test_missing_inputs_are_not_inferred_from_as_at_dates_or_contract_examples() -> None:
    payload = json.loads(READINESS.read_text())
    assert payload["blockers"] == [
        "event_time_intervals_missing",
        "non_legislation_historical_sources_missing",
    ]
    assert payload["status"] == "blocked_missing_source_pack_inputs"
