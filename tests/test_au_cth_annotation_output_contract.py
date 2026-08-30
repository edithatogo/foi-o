import json
from pathlib import Path

import pytest

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


def test_valid_annotation_output_contract(tmp_path: Path) -> None:
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(_record()), encoding="utf-8")
    assert not validate_json_schema(path, SCHEMA).errors


def test_rejects_wrong_jurisdiction_and_candidate_visibility(tmp_path: Path) -> None:
    record = _record()
    record.update(jurisdiction="AU-NSW", blinded_to_candidate=False)
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    errors = validate_json_schema(path, SCHEMA).errors
    assert len(errors) >= 2


def test_abstention_requires_unknown_null_span_and_reason(tmp_path: Path) -> None:
    record = _record()
    record.update(
        label="unknown", spans=[], abstention=True, abstention_reason="insufficient_evidence"
    )
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert not validate_json_schema(path, SCHEMA).errors

    # Invalid: abstention with non-empty span
    record["spans"] = [{"start": 0, "end": 1, "coordinate_system": "utf8_character_half_open"}]
    path.write_text(json.dumps(record), encoding="utf-8")
    assert validate_json_schema(path, SCHEMA).errors


@pytest.mark.parametrize(
    "invalid_span",
    [
        {"start": -1, "end": 10, "coordinate_system": "utf8_character_half_open"},
        {"start": 0, "end": 0, "coordinate_system": "utf8_character_half_open"},
        {"start": 0, "end": 10, "coordinate_system": "byte_offset"},
    ],
)
def test_narrow_span_negative_schema_fixtures(
    invalid_span: dict[str, object], tmp_path: Path
) -> None:
    record = _record()
    record["spans"] = [invalid_span]
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    errors = validate_json_schema(path, SCHEMA).errors
    assert len(errors) >= 1


def test_span_inverted_or_empty_rejected_by_validator() -> None:
    from foi_o_nz.australian_subset_annotation import validate_annotation_record

    record = _record()
    record["role"] = "automated-agent-role-a"
    record["unit_id"] = "au-cth-unit-001"
    record["span"] = {"start": 5, "end": 5, "coordinate_system": "utf8_character_half_open"}
    with pytest.raises(ValueError, match="span bounds"):
        validate_annotation_record(record, expected_role="automated-agent-role-a")

    record["span"] = {"start": 10, "end": 5, "coordinate_system": "utf8_character_half_open"}
    with pytest.raises(ValueError, match="span bounds"):
        validate_annotation_record(record, expected_role="automated-agent-role-a")


def test_whole_document_negative_fixtures_max_spans(tmp_path: Path) -> None:
    record = _record()
    # Excessive number of spans (more than 3 max items)
    record["spans"] = [
        {"start": 0, "end": 10, "coordinate_system": "utf8_character_half_open"},
        {"start": 20, "end": 30, "coordinate_system": "utf8_character_half_open"},
        {"start": 40, "end": 50, "coordinate_system": "utf8_character_half_open"},
        {"start": 60, "end": 70, "coordinate_system": "utf8_character_half_open"},
    ]
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    errors = validate_json_schema(path, SCHEMA).errors
    assert len(errors) >= 1


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("target_assertion", "nsw_gipa_access_matter"),
        ("target_assertion", "generic_foi_matter"),
        ("evidence_window", "whole_repository_context"),
        ("annotator_id", "human-reviewer-alice"),
        ("annotator_id", "unauthenticated_agent"),
    ],
)
def test_ambiguous_au_cth_identity_negative_fixtures(
    field: str, bad_value: str, tmp_path: Path
) -> None:
    record = _record()
    record[field] = bad_value
    path = tmp_path / "au-cth-annotation.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    errors = validate_json_schema(path, SCHEMA).errors
    assert len(errors) >= 1
