import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/au-cth-annotation-output.schema.json"


def _record() -> dict[str, object]:
    return {
        "schema_version": "foi-o.au-cth-annotation-output.v0.1.0",
        "record_id": "au-cth-unit-001",
        "unit_sha256": "a" * 64,
        "annotator_id": "automated-agent-role-a",
        "codebook_revision": "b" * 40,
        "jurisdiction": "AU-CTH",
        "target_assertion": "au_cth_commonwealth_foi_matter",
        "evidence_window": "captured request-page text only",
        "label": "observed",
        "spans": [{"start": 0, "end": 12, "coordinate_system": "utf8_character_half_open"}],
        "abstention": False,
        "abstention_reason": None,
        "blinded_to_candidate": True,
    }


def test_valid_annotation_output_contract() -> None:
    path = ROOT / "tests/.tmp-au-cth-annotation.json"
    try:
        path.write_text(json.dumps(_record()), encoding="utf-8")
        assert not validate_json_schema(path, SCHEMA).errors
    finally:
        path.unlink(missing_ok=True)


def test_rejects_wrong_jurisdiction_and_candidate_visibility() -> None:
    record = _record()
    record.update(jurisdiction="AU-NSW", blinded_to_candidate=False)
    path = ROOT / "tests/.tmp-au-cth-annotation.json"
    try:
        path.write_text(json.dumps(record), encoding="utf-8")
        errors = validate_json_schema(path, SCHEMA).errors
        assert len(errors) >= 2
    finally:
        path.unlink(missing_ok=True)


def test_abstention_requires_unknown_null_span_and_reason() -> None:
    record = _record()
    record.update(
        label="unknown", spans=[], abstention=True, abstention_reason="insufficient_evidence"
    )
    path = ROOT / "tests/.tmp-au-cth-annotation.json"
    try:
        path.write_text(json.dumps(record), encoding="utf-8")
        assert not validate_json_schema(path, SCHEMA).errors
        record["spans"] = [{"start": 0, "end": 1, "coordinate_system": "utf8_character_half_open"}]
        path.write_text(json.dumps(record), encoding="utf-8")
        assert validate_json_schema(path, SCHEMA).errors
    finally:
        path.unlink(missing_ok=True)
