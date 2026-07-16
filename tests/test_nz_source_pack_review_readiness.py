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
INTERVALS = ROOT / "mappings/nz-oia-applicability-interval-candidates.yaml"
NONLEG = ROOT / "examples/v2/nz-nonlegislation-source-manifest.2026-07-16.json"


def test_source_pack_readiness_is_schema_valid_and_fail_closed() -> None:
    result = validate_json_schema(READINESS, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(READINESS.read_text())
    assert payload["source_pack_ready"] is False
    assert payload["source_pack_promotion_allowed"] is False
    assert payload["event_time_intervals"]["interval_count"] == 50
    assert payload["event_time_intervals"]["human_approved"] is False
    assert payload["non_legislation_sources"]["artifact_count"] == 7
    assert payload["non_legislation_sources"]["human_approved"] is False


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


def test_acquired_candidates_are_exactly_pinned_without_inferred_approval() -> None:
    payload = json.loads(READINESS.read_text())
    assert payload["event_time_intervals"]["artifact_sha256"] == sha256(
        INTERVALS.read_bytes()
    ).hexdigest()
    assert payload["non_legislation_sources"]["manifest_sha256"] == sha256(
        NONLEG.read_bytes()
    ).hexdigest()
    assert payload["provider_scope_interpretation"]["existing_registry_approved"] is True
    assert payload["provider_scope_interpretation"]["psc_scope_approved"] is False
    assert payload["blockers"] == [
        "event_time_human_review_pending",
        "psc_provider_scope_review_pending",
        "nonleg_source_selection_review_pending",
        "source_pack_promotion_pending",
    ]
    assert payload["status"] == "candidate_inputs_acquired_human_review_pending"
