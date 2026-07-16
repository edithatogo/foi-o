"""Tests for the consolidated pending empirical human-gate review packet."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/empirical-human-gate-review-packet.pending.json"
SCHEMA = ROOT / "schemas/json/empirical-human-gate-review-packet.schema.json"


def test_human_gate_packet_is_schema_valid_and_pending() -> None:
    result = validate_json_schema(PACKET, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(PACKET.read_text())
    assert payload["status"] == "pending_named_human_review"
    assert payload["reviewer"] is None
    assert payload["reviewed_at"] is None
    assert payload["source_pack_promotion_allowed"] is False
    assert payload["sample_freeze_allowed"] is False
    assert payload["empirical_comparison_allowed"] is False


def test_every_review_artifact_is_exactly_hash_pinned() -> None:
    payload = json.loads(PACKET.read_text())
    for review in payload["reviews"]:
        path = ROOT / review["artifact_path"]
        assert path.is_file()
        assert review["artifact_sha256"] == sha256(path.read_bytes()).hexdigest()
        assert review["decision"] == "pending"
        assert review["approver"] is None
        assert review["reviewed_at"] is None


def test_packet_does_not_convert_rights_terms_into_provider_scope_approval() -> None:
    payload = json.loads(PACKET.read_text())
    provider = next(
        review for review in payload["reviews"] if review["review_id"] == "psc-provider-scope"
    )
    assert provider["rights_evidence_sha256"] == (
        "2ad002bf09eb0f22fc9fd46bf944213f9538b8437d05f36b925a9c6e180d4ccb"
    )
    assert provider["rights_evidence_byte_size"] == 37456
    assert provider["proposed_scope"] == "publicservice.govt.nz provider-owned content"
    assert provider["decision"] == "pending"


def test_annotation_roles_and_execution_inputs_are_unassigned() -> None:
    payload = json.loads(PACKET.read_text())
    roles = payload["annotation_roles"]
    assert roles["annotator_ids"] == []
    assert roles["adjudicator_id"] is None
    assert roles["role_assignment_approved"] is False
    assert payload["execution_inputs"] == {
        "rights_approved_source_population_manifest": None,
        "approved_codebook_revision": None,
        "approved_sampling_configuration": None,
    }


def test_raw_state_review_cannot_cure_missing_attachment_evidence() -> None:
    payload = json.loads(PACKET.read_text())
    raw_state = next(
        review for review in payload["reviews"] if review["review_id"] == "bounded-raw-state-mapping"
    )
    assert raw_state["candidate_mapping"] == {
        "raw_state": "waiting_response",
        "normalised_state": "awaiting_response",
    }
    assert raw_state["attachment_count"] == 0
    assert raw_state["archive_wide_claim_allowed"] is False


def test_attachment_snapshot_requires_exact_bounded_rights_review() -> None:
    payload = json.loads(PACKET.read_text())
    snapshot = next(
        review for review in payload["reviews"] if review["review_id"] == "attachment-snapshot-rights"
    )
    assert snapshot["snapshot_manifest_sha256"] == (
        "42f8ed87738a31b857d37c94772fa8471890ce8f6caa81af5690f3b6f6fa707b"
    )
    assert snapshot["request_id"] == "11872"
    assert snapshot["attachment_count"] == 3
    assert snapshot["attachment_bytes"] == 13_259_266
    assert snapshot["rights_status"] == "pending"
    assert snapshot["decision"] == "pending"
