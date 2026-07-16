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
    assert audit["upstreams"]["nlp_policy_nz"]["fixture_record_count"] == 2
    assert audit["upstreams"]["nlp_policy_nz"]["fixture_is_synthetic"] is True
    assert audit["upstreams"]["nlp_policy_nz"]["raw_manifest_entrypoint_available"] is False
    assert audit["contract_alignment"]["compatible"] is False
    assert audit["blockers"] == sorted(audit["blockers"])


def test_audit_pins_real_revisions_and_rejects_placeholder_evidence() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    for upstream in audit["upstreams"].values():
        assert len(upstream["repository_revision"]) == 40
        assert set(upstream["repository_revision"]) != {"a"}
    nlp = audit["upstreams"]["nlp_policy_nz"]
    assert nlp["fixture_uses_placeholder_archive_revision"] is True
    assert nlp["fixture_uses_placeholder_source_digest"] is True
    assert nlp["real_model_pin_available"] is False
