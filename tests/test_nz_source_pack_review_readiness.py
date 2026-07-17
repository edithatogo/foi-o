"""Tests for the reconciled NZ source-pack human review boundary."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
READINESS = ROOT / "examples/v2/nz-source-pack-review-readiness.2026-07-16.json"
SCHEMA = ROOT / "schemas/json/nz-source-pack-review-readiness.schema.json"
APPROVAL = ROOT / "examples/v2/human-promotion-review-packet.approved.json"
INTERVALS = ROOT / "mappings/nz-oia-applicability-interval-candidates.yaml"
NONLEG = ROOT / "examples/v2/nz-nonlegislation-source-manifest.2026-07-16.json"
INTERVAL_REVIEW = ROOT / "examples/v2/nz-oia-applicability-interval-review.approved.json"
INTERVAL_REVIEW_SCHEMA = ROOT / "schemas/json/nz-oia-applicability-interval-review.schema.json"


def test_source_pack_readiness_is_schema_valid_and_fail_closed() -> None:
    result = validate_json_schema(READINESS, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(READINESS.read_text())
    assert payload["source_pack_ready"] is False
    assert payload["source_pack_promotion_allowed"] is False
    assert payload["event_time_intervals"]["interval_count"] == 50
    assert payload["event_time_intervals"]["human_approved"] is True
    assert (
        payload["event_time_intervals"]["review_artifact_sha256"]
        == sha256(INTERVAL_REVIEW.read_bytes()).hexdigest()
    )
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
    assert (
        payload["event_time_intervals"]["artifact_sha256"]
        == sha256(INTERVALS.read_bytes()).hexdigest()
    )
    assert (
        payload["non_legislation_sources"]["manifest_sha256"]
        == sha256(NONLEG.read_bytes()).hexdigest()
    )
    assert payload["provider_scope_interpretation"]["existing_registry_approved"] is True
    assert payload["provider_scope_interpretation"]["psc_scope_approved"] is False
    assert payload["blockers"] == [
        "psc_provider_scope_review_pending",
        "nonleg_source_selection_review_pending",
        "source_pack_promotion_pending",
    ]
    assert payload["status"] == "candidate_inputs_acquired_human_review_pending"


def test_interval_review_is_exactly_pinned_and_does_not_promote_source_pack() -> None:
    result = validate_json_schema(INTERVAL_REVIEW, INTERVAL_REVIEW_SCHEMA)
    assert not result.errors, result.errors
    review = json.loads(INTERVAL_REVIEW.read_text())
    assert review["reviewer"] == "edithatogo"
    assert review["interval_count"] == 50
    assert review["candidate_artifact_sha256"] == sha256(INTERVALS.read_bytes()).hexdigest()
    assert review["all_boundaries_approved"] is True
    assert review["source_pack_promotion_allowed"] is False
    assert all(value is False for value in review["prohibited_actions"].values())


@pytest.mark.parametrize(
    "mutation",
    ["candidate_hash", "source_pack_promotion", "broader_legal_certification"],
)
def test_interval_review_rejects_scope_or_evidence_expansion(tmp_path: Path, mutation: str) -> None:
    review = json.loads(INTERVAL_REVIEW.read_text())
    if mutation == "candidate_hash":
        review["candidate_artifact_sha256"] = "0" * 64
    elif mutation == "source_pack_promotion":
        review["source_pack_promotion_allowed"] = True
    else:
        review["prohibited_actions"]["legal_certification_beyond_reviewed_boundaries"] = True
    invalid = tmp_path / "interval-review.json"
    invalid.write_text(json.dumps(review), encoding="utf-8")
    result = validate_json_schema(invalid, INTERVAL_REVIEW_SCHEMA)
    assert result.errors
