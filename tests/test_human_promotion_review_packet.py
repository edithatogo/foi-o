"""Fail-closed checks for the human promotion review packet."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas" / "json" / "human-promotion-review-packet.schema.json"
PACKET = ROOT / "examples" / "v2" / "human-promotion-review-packet.approved.json"


def test_review_packet_is_schema_valid_and_approved() -> None:
    result = validate_json_schema(PACKET, SCHEMA)
    assert not result.errors, result.errors
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["overall_status"] == "approved"
    assert packet["promotion_allowed"] is True
    assert packet["reviewer"]["reviewer_id"] == "edithatogo"
    assert packet["reviewer"]["reviewed_at"] == "2026-07-16T09:34:52Z"
    assert [item["decision"] for item in packet["items"]] == ["approved"] * len(packet["items"])


def test_review_items_pin_current_artifacts_and_separate_decision_kinds() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert {item["decision_kind"] for item in packet["items"]} == {
        "fixture_promotion",
        "legal_mapping_approval",
        "rights_scope_approval",
    }
    for item in packet["items"]:
        artifact = ROOT / item["artifact_path"]
        assert artifact.is_file()
        assert sha256(artifact.read_bytes()).hexdigest() == item["artifact_sha256"]
        assert item["promotion_allowed"] is True


def test_schema_examples_are_explicitly_not_approval_evidence() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["excluded_evidence"] == [
        {
            "path_glob": "examples/v2/schema-valid/*.json",
            "reason": "contract_fixtures_not_human_approval_evidence",
        }
    ]
