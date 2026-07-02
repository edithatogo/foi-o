from __future__ import annotations

from pathlib import Path

from foi_o_nz.quality import assess_events
from foi_o_nz.validation import validate_json_schema

QUALITY_REPORT_SCHEMA = Path("schemas/json/quality-report.schema.json")


def test_quality_gate_flags_dispositive_without_certification_metadata() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:bad",
                "event_type": "ReleaseMade",
                "assertion_status": "inferred",
                "machine_generated": True,
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    )

    assert not result["ok"]
    assert result["error_count"] >= 1


def test_quality_gate_accepts_observed_event() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:ok",
                "event_type": "RequestObserved",
                "assertion_status": "observed",
                "machine_generated": True,
                "generator": {"system": "foi-o-nz"},
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    )

    assert result["ok"]


def test_quality_gate_flags_stale_or_unversioned_legal_references() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:stale-ref",
                "event_type": "ReleaseMade",
                "assertion_status": "inferred",
                "machine_generated": True,
                "generator": {"system": "foi-o-nz"},
                "requires_human_certification": True,
                "human_certification": {"certified": False},
                "evidence": [{"evidence_id": "e1"}],
                "legal_references": [
                    {
                        "source_id": "nz.oia.act",
                        "title": "Official Information Act 1982",
                        "reference": "s 15",
                        "source_status": "external_gate",
                    }
                ],
            }
        ]
    )

    codes = {finding["code"] for finding in result["findings"]}
    assert result["ok"]
    assert "unversioned_legal_reference" in codes
    assert "stale_or_unverified_legal_reference" in codes


def test_quality_report_states_metadata_checks_are_not_legal_certainty() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:ok",
                "event_type": "RequestObserved",
                "assertion_status": "observed",
                "machine_generated": True,
                "generator": {"system": "foi-o-nz"},
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    )

    assert any("do not certify legal correctness" in item for item in result["limitations"])


def test_committed_quality_report_example_is_schema_valid() -> None:
    validation = validate_json_schema(
        Path("examples/quality-report.legal-reference-warning.json"),
        QUALITY_REPORT_SCHEMA,
    )

    assert validation.ok, validation.errors
