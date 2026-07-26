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
CTH_EVIDENCE = ROOT / "examples/v2/australian-source-evidence-au-cth.2026-07-26.json"
CTH_EVIDENCE_SHA256 = hashlib.sha256(CTH_EVIDENCE.read_bytes()).hexdigest()
EVIDENCE_BY_PACK = {
    "australian-source-pack-au-cth.candidate.json": EVIDENCE_SHA256,
    "australian-source-pack-au-nsw.candidate.json": EVIDENCE_SHA256,
    "australian-source-pack-au-cth-2026-07-26.candidate.json": CTH_EVIDENCE_SHA256,
}


def test_candidate_packs_are_schema_valid_and_pin_the_evidence_manifest() -> None:
    for path in sorted(ROOT.glob("examples/v2/australian-source-pack-*.candidate.json")):
        result = validate_json_schema(path, SCHEMA)
        assert not result.errors, result.errors
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["rights_review_status"] == "approved"
        assert payload["source_manifest_sha256"] == EVIDENCE_BY_PACK[path.name]


def test_current_cth_candidate_pins_jurisdiction_isolated_evidence() -> None:
    payload = json.loads(CTH_EVIDENCE.read_text(encoding="utf-8"))
    assert payload["jurisdiction"] == "AU-CTH"
    assert payload["source_count"] == 1
    assert {source["jurisdiction"] for source in payload["sources"]} == {"AU-CTH"}
    assert all(source["content_sha256"] for source in payload["sources"])
    assert payload["rights_review"]["scope"] == (
        "bounded local empirical validation and immutable archival only"
    )


def test_source_evidence_fails_closed_for_unretrieved_nsw_content() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    sources = {source["jurisdiction"]: source for source in payload["sources"]}
    assert sources["AU-CTH"]["content_sha256"]
    assert sources["AU-NSW"]["content_sha256"] is None
    assert sources["AU-NSW"]["acquisition_status"] == "direct_cli_retrieval_blocked_http_403"


def test_capture_preflight_is_pinned_and_execution_closed() -> None:
    packet_path = ROOT / "examples/v2/australian-capture-preflight.pending.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["execution_allowed"] is False
    assert packet["scope"]["jurisdictions"] == ["NSW", "FEDERAL"]
    assert packet["authorization"]["execution_authorized_by_record"] is True
    assert packet["status"] == "capture_attempted_source_access_blocked"
    assert packet["execution_allowed"] is False
    for jurisdiction, pin in packet["source_pack_pins"].items():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
        assert packet["source_pack_pins"][jurisdiction]["rights_review_status"] == "approved"
