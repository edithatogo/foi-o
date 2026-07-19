import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/locked-annotation-record.schema.json"


def _record() -> dict[str, object]:
    return {
        "schema_version": "foi-o.locked-annotation-record.v0.1.0",
        "record_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "unit_sha256": "a" * 64,
        "annotator_id": "fixture:not-human",
        "codebook_revision": "b" * 40,
        "label": "fixture-label",
        "span": {"start": 0, "end": 1, "coordinate_system": "utf8_character_half_open"},
        "uncertainty": 0.5,
        "abstention": False,
        "abstention_reason": None,
        "notes": "Schema fixture only; not an annotation.",
        "blinded_to_candidate": True,
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": None,
    }


def test_candidate_annotation_fixture_is_not_empirical(tmp_path: Path) -> None:
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(_record()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_locked_annotation_rejects_agent_identity(tmp_path: Path) -> None:
    payload = _record()
    payload.update(
        status="locked_human_annotation",
        empirical_evidence=True,
        annotator_id="agent:reviewer-1",
        locked_at="2026-07-17T01:00:00Z",
    )
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_locked_analyst_analysis_accepts_agent_identity(tmp_path: Path) -> None:
    payload = _record()
    payload.update(
        schema_version="foi-o.locked-analysis-record.v0.2.0",
        status="locked_analyst_analysis",
        empirical_evidence=True,
        annotator_id="agent:analyst-1",
        locked_at="2026-07-19T01:00:00Z",
    )
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps(payload))
    assert not validate_json_schema(path, SCHEMA).errors


def test_abstention_requires_controlled_reason_and_null_outputs(tmp_path: Path) -> None:
    payload = _record()
    payload.update(abstention=True, label=None, span=None, abstention_reason=None)
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors

    payload["abstention_reason"] = "missing_evidence"
    path.write_text(json.dumps(payload))
    assert not validate_json_schema(path, SCHEMA).errors


def test_non_abstention_requires_label(tmp_path: Path) -> None:
    payload = _record()
    payload["label"] = None
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors
