"""Integrity tests for candidate Australian source-pack provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/json/jurisdiction-source-pack.schema.json"
EVIDENCE = ROOT / "examples/v2/australian-source-evidence-candidate.2026-07-21.json"
EVIDENCE_SHA256 = hashlib.sha256(EVIDENCE.read_bytes()).hexdigest()


def test_candidate_packs_are_schema_valid_and_pin_the_evidence_manifest() -> None:
    for path in sorted(ROOT.glob("examples/v2/australian-source-pack-*.candidate.json")):
        result = validate_json_schema(path, SCHEMA)
        assert not result.errors, result.errors
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["rights_review_status"] == "pending"
        assert payload["source_manifest_sha256"] == EVIDENCE_SHA256


def test_source_evidence_fails_closed_for_unretrieved_nsw_content() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    sources = {source["jurisdiction"]: source for source in payload["sources"]}
    assert sources["AU-CTH"]["content_sha256"]
    assert sources["AU-NSW"]["content_sha256"] is None
    assert sources["AU-NSW"]["acquisition_status"] == "direct_cli_retrieval_blocked_http_403"
