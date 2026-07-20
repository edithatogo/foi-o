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
PSC_REVIEW = ROOT / "examples/v2/psc-provider-scope-review.approved.json"
PSC_REVIEW_SCHEMA = ROOT / "schemas/json/psc-provider-scope-review.schema.json"
SOURCE_REVIEW = ROOT / "examples/v2/nz-nonlegislation-source-review.approved.json"
SOURCE_REVIEW_SCHEMA = ROOT / "schemas/json/nz-nonlegislation-source-review.schema.json"
PROMOTION = ROOT / "examples/v2/nz-source-pack-promotion.approved.json"
PROMOTION_SCHEMA = ROOT / "schemas/json/nz-source-pack-promotion.schema.json"
GOVERNED_PACK = ROOT / "examples/v2/nz-source-pack.governed-metadata.json"
GOVERNED_PACK_SCHEMA = ROOT / "schemas/json/nz-source-pack-governed-metadata.schema.json"


def test_source_pack_readiness_is_schema_valid_and_fail_closed() -> None:
    result = validate_json_schema(READINESS, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(READINESS.read_text())
    assert payload["source_pack_ready"] is True
    assert payload["source_pack_promotion_allowed"] is True
    assert payload["event_time_intervals"]["interval_count"] == 50
    assert payload["event_time_intervals"]["human_approved"] is True
    assert (
        payload["event_time_intervals"]["review_artifact_sha256"]
        == sha256(INTERVAL_REVIEW.read_bytes()).hexdigest()
    )
    assert payload["non_legislation_sources"]["artifact_count"] == 7
    assert payload["non_legislation_sources"]["human_approved"] is True
    assert (
        payload["non_legislation_sources"]["review_artifact_sha256"]
        == sha256(SOURCE_REVIEW.read_bytes()).hexdigest()
    )


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
    assert payload["provider_scope_interpretation"]["psc_scope_approved"] is True
    assert (
        payload["provider_scope_interpretation"]["review_artifact_sha256"]
        == sha256(PSC_REVIEW.read_bytes()).hexdigest()
    )
    assert payload["blockers"] == []
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


def test_psc_provider_scope_review_is_exact_and_exclusion_bounded() -> None:
    result = validate_json_schema(PSC_REVIEW, PSC_REVIEW_SCHEMA)
    assert not result.errors, result.errors
    review = json.loads(PSC_REVIEW.read_text())
    assert review["terms_evidence_sha256"] == (
        "2ad002bf09eb0f22fc9fd46bf944213f9538b8437d05f36b925a9c6e180d4ccb"
    )
    assert review["provider_scope"] == "publicservice.govt.nz provider-owned content"
    assert len(review["exclusions"]) == 6
    assert review["attribution_required"] is True
    assert all(value is False for value in review["prohibited_actions"].values())


@pytest.mark.parametrize("mutation", ["terms_hash", "exclusion", "publication"])
def test_psc_provider_scope_review_rejects_expansion(tmp_path: Path, mutation: str) -> None:
    review = json.loads(PSC_REVIEW.read_text())
    if mutation == "terms_hash":
        review["terms_evidence_sha256"] = "0" * 64
    elif mutation == "exclusion":
        review["exclusions"].pop()
    else:
        review["prohibited_actions"]["publication"] = True
    invalid = tmp_path / "psc-review.json"
    invalid.write_text(json.dumps(review), encoding="utf-8")
    result = validate_json_schema(invalid, PSC_REVIEW_SCHEMA)
    assert result.errors


def test_seven_source_review_is_exact_and_rights_bounded() -> None:
    result = validate_json_schema(SOURCE_REVIEW, SOURCE_REVIEW_SCHEMA)
    assert not result.errors, result.errors
    review = json.loads(SOURCE_REVIEW.read_text())
    assert review["manifest_sha256"] == sha256(NONLEG.read_bytes()).hexdigest()
    assert review["source_count"] == 7
    assert review["selection_approved"] is True
    assert review["historical_applicability_approved"] is True
    assert all(value is False for value in review["prohibited_actions"].values())


@pytest.mark.parametrize("mutation", ["manifest_hash", "rights", "promotion"])
def test_seven_source_review_rejects_expansion(tmp_path: Path, mutation: str) -> None:
    review = json.loads(SOURCE_REVIEW.read_text())
    if mutation == "manifest_hash":
        review["manifest_sha256"] = "0" * 64
    elif mutation == "rights":
        review["rights_expanded"] = True
    else:
        review["prohibited_actions"]["source_pack_promotion"] = True
    invalid = tmp_path / "source-review.json"
    invalid.write_text(json.dumps(review), encoding="utf-8")
    assert validate_json_schema(invalid, SOURCE_REVIEW_SCHEMA).errors


def test_promoted_source_pack_is_metadata_only_and_rights_bounded() -> None:
    assert not validate_json_schema(PROMOTION, PROMOTION_SCHEMA).errors
    assert not validate_json_schema(GOVERNED_PACK, GOVERNED_PACK_SCHEMA).errors
    promotion = json.loads(PROMOTION.read_text())
    pack = json.loads(GOVERNED_PACK.read_text())
    assert promotion["reviewed_readiness_sha256"] == (
        "a2ceffc2004324e3c31ead67f44fb46f44dbe8f3617ce32154c55d3daff4e00a"
    )
    assert pack["source_content_included"] is False
    assert pack["source_count"] == 7
    assert pack["interval_count"] == 50
    for path_field, hash_field in (
        ("promotion_path", "promotion_sha256"),
        ("source_manifest_path", "source_manifest_sha256"),
        ("source_review_path", "source_review_sha256"),
        ("interval_review_path", "interval_review_sha256"),
        ("psc_review_path", "psc_review_sha256"),
        ("rights_registry_path", "rights_registry_sha256"),
    ):
        assert pack[hash_field] == sha256((ROOT / pack[path_field]).read_bytes()).hexdigest()
    assert pack["attribution_required"] is True
    assert len(pack["exclusions"]) == 6
    assert all(value is False for value in pack["prohibited_actions"].values())


@pytest.mark.parametrize("mutation", ["content", "attribution", "exclusion", "hash", "publication"])
def test_promoted_pack_rejects_rights_or_content_drift(tmp_path: Path, mutation: str) -> None:
    pack = json.loads(GOVERNED_PACK.read_text())
    if mutation == "content":
        pack["source_content_included"] = True
    elif mutation == "attribution":
        pack["attribution_required"] = False
    elif mutation == "exclusion":
        pack["exclusions"].pop()
    elif mutation == "hash":
        pack["psc_review_sha256"] = "0" * 64
    else:
        pack["prohibited_actions"]["publication"] = True
    invalid = tmp_path / "pack.json"
    invalid.write_text(json.dumps(pack), encoding="utf-8")
    assert validate_json_schema(invalid, GOVERNED_PACK_SCHEMA).errors
