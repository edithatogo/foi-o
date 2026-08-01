from __future__ import annotations

import pytest

from foi_o_nz.australian_subset_annotation import _annotate, validate_annotation_record


def test_automated_role_marks_explicit_foi_as_observed() -> None:
    result = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    assert result["label"] == "observed"
    assert result["abstention"] is False


def test_automated_role_abstains_without_supported_text() -> None:
    result = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "No relevant wording",
        role="agent:au-cth-annotator-b",
    )
    assert result["label"] == "unknown"
    assert result["abstention"] is True


def test_annotation_record_validator_accepts_bounded_record() -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


@pytest.mark.parametrize(
    ("field", "value"),
    [("role", "agent:au-cth-adjudicator"), ("label", "invented"), ("unit_id", "")],
)
def test_annotation_record_validator_rejects_role_label_and_identity_drift(
    field: str, value: object
) -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    record[field] = value
    with pytest.raises(ValueError, match=r"mismatch|approved codebook|identity"):
        validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


def test_annotation_record_validator_rejects_abstention_with_span() -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "No relevant wording",
        role="agent:au-cth-annotator-a",
    )
    record["span"] = {"start": 0, "end": 1, "coordinate_system": "utf8_character_half_open"}
    with pytest.raises(ValueError, match="abstention span"):
        validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")
