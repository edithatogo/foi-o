"""Tests for the pre-annotation human approval boundary."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/annotation-protocol-review-readiness.2026-07-16.json"
SCHEMA = ROOT / "schemas/json/annotation-protocol-review-readiness.schema.json"


def test_annotation_protocol_packet_is_schema_valid_and_hash_pinned() -> None:
    result = validate_json_schema(PACKET, SCHEMA)
    assert not result.errors, result.errors
    packet = json.loads(PACKET.read_text())
    protocol = ROOT / packet["protocol_path"]
    assert packet["protocol_sha256"] == sha256(protocol.read_bytes()).hexdigest()
    review = ROOT / packet["protocol_review_path"]
    assert packet["protocol_review_sha256"] == sha256(review.read_bytes()).hexdigest()


def test_protocol_is_approved_but_execution_remains_fail_closed() -> None:
    packet = json.loads(PACKET.read_text())
    assert packet["protocol_decision"] == "approved"
    assert packet["protocol_approver"] == "edithatogo"
    assert packet["protocol_reviewed_at"] == "2026-07-17T09:48:28Z"
    assert packet["annotator_ids"] == []
    assert packet["adjudicator_id"] is None
    assert packet["source_population_manifest"] is None
    assert packet["codebook_revision"] is None
    assert packet["sampling_configuration"] is None
    assert packet["ready_to_freeze_sample"] is False
    assert packet["promotion_allowed"] is False
    assert packet["blockers"] == [
        "two_independent_annotators_missing",
        "adjudicator_missing",
        "rights_approved_source_population_missing",
        "codebook_revision_missing",
        "sampling_configuration_missing",
    ]


def test_protocol_approval_is_bounded_and_schema_valid() -> None:
    packet = json.loads(PACKET.read_text())
    review = ROOT / packet["protocol_review_path"]
    schema = ROOT / "schemas/json/annotation-protocol-review.schema.json"
    result = validate_json_schema(review, schema)
    assert not result.errors, result.errors
    payload = json.loads(review.read_text())
    assert payload["protocol_design_approved"] is True
    assert payload["execution_authorized"] is False
    assert not any(payload["prohibited_actions"].values())


def test_protocol_forbids_placeholder_or_ai_generated_empirical_evidence() -> None:
    text = (ROOT / "docs/41-v2-sampling-and-annotation-protocol.md").read_text().lower()
    assert "two distinct human annotators" in text
    assert "one distinct adjudicator" in text
    assert "ai-proposed labels" in text
    assert "not substitutes" in text
    assert "not an empirical sample" in text
    assert "half-open `[start, end)`" in text
    assert "cluster-bootstrap confidence intervals" in text
    assert "sequential stages" in " ".join(text.split())
