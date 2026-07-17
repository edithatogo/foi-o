import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/adjudication-record.schema.json"


def _record() -> dict[str, object]:
    return {
        "schema_version": "foi-o.adjudication-record.v0.1.0",
        "record_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "unit_sha256": "a" * 64,
        "annotation_refs": [
            {"annotator_id": "fixture:not-human-1", "sha256": "b" * 64},
            {"annotator_id": "fixture:not-human-2", "sha256": "c" * 64},
        ],
        "adjudicator_id": "fixture:not-human-adjudicator",
        "outcome": "unresolved",
        "adjudicated_label": None,
        "adjudicated_span": None,
        "rationale": "Schema fixture only; no adjudication occurred.",
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": None,
    }


def test_candidate_adjudication_fixture_is_not_empirical(tmp_path: Path) -> None:
    path = tmp_path / "adjudication.json"
    path.write_text(json.dumps(_record()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_locked_adjudication_rejects_agent_identity(tmp_path: Path) -> None:
    payload = _record()
    payload.update(
        status="locked_human_adjudication",
        empirical_evidence=True,
        adjudicator_id="agent:adjudicator",
        locked_at="2026-07-17T01:00:00Z",
    )
    path = tmp_path / "adjudication.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_resolved_adjudication_requires_label(tmp_path: Path) -> None:
    payload = _record()
    payload["outcome"] = "resolved"
    path = tmp_path / "adjudication.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors

    payload["adjudicated_label"] = "approved-label"
    path.write_text(json.dumps(payload))
    assert not validate_json_schema(path, SCHEMA).errors
