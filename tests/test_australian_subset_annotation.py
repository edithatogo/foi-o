from __future__ import annotations

from foi_o_nz.australian_subset_annotation import _annotate


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
