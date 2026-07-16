"""Contract tests for the evidence-pinned upstream extraction readiness audit."""

from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas" / "json" / "upstream-extraction-readiness.schema.json"
AUDIT = ROOT / "examples" / "v2" / "upstream-extraction-readiness.2026-07-16.json"


def test_upstream_readiness_audit_is_schema_valid_and_fail_closed() -> None:
    result = validate_json_schema(AUDIT, SCHEMA)
    assert not result.errors, result.errors
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["ready_for_governed_reextraction"] is False
    assert audit["source_records_modified"] is False
    assert audit["upstreams"]["fyi_archive"]["verified_record_count"] == 33217
    local = audit["upstreams"]["fyi_archive"]["approved_local_content_snapshot"]
    assert local["content_bearing"] is True
    assert local["published"] is False
    assert local["redistribution_allowed"] is False
    assert local["purpose"] == "foi-o-candidate-extraction"
    assert (
        local["reviewed_pending_manifest_sha256"]
        == "d850ca367c2069d7e6d9ac39e8534779d0f64f2b3d708d36f773c0e3a2e271e3"
    )
    assert (
        local["approved_manifest_sha256"]
        == "c929b312f4b627049b7867e46fa74b08ed8e9a43c35ba866871bead6f8a19b7d"
    )
    assert audit["upstreams"]["nlp_policy_nz"]["fixture_record_count"] == 2
    assert audit["upstreams"]["nlp_policy_nz"]["fixture_is_synthetic"] is True
    assert audit["upstreams"]["nlp_policy_nz"]["raw_manifest_entrypoint_available"] is True
    assert audit["contract_alignment"]["compatible"] is True
    assert audit["blockers"] == sorted(audit["blockers"])
    assert "rights_metadata_incomplete" not in audit["blockers"]
    assert "approved_snapshot_adapter_pending" not in audit["blockers"]
    baseline = audit["upstreams"]["nlp_policy_nz"]["initial_baseline"]
    assert baseline["artifact_sha256"] == (
        "90550ce084be684ee493e2ce7470cbe0b01dee13b6253c50f91c7de9974d6007"
    )
    assert baseline["verification_report_sha256"] == (
        "0702d54e59c966958a759eb03f28018c96d197f27b948febf3374c3da4a6fcbc"
    )
    assert baseline["review_status"] == "candidate"
    assert baseline["model_applied"] is False
    assert baseline["published"] is False


def test_audit_pins_real_revisions_and_rejects_placeholder_evidence() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    for upstream in audit["upstreams"].values():
        assert len(upstream["repository_revision"]) == 40
        assert set(upstream["repository_revision"]) != {"a"}
    nlp = audit["upstreams"]["nlp_policy_nz"]
    assert nlp["fixture_uses_placeholder_archive_revision"] is True
    assert nlp["fixture_uses_placeholder_source_digest"] is True
    assert nlp["real_model_pin_available"] is True
    assert nlp["model_applied_during_candidate_extraction"] is False
    assert len(nlp["model"]["revision"]) == 40
    assert len(nlp["model"]["weights_sha256"]) == 64
