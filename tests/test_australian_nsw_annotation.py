from __future__ import annotations

from foi_o_nz.australian_nsw_annotation import _annotate


def test_nsw_annotator_observes_gipa_text() -> None:
    unit = {"unit_id": "AU-NSW:x", "text_sha256": "a" * 64, "text": "A GIPA request"}
    assert _annotate(unit, role="agent:au-nsw-annotator-a")["label"] == "observed"


def test_nsw_annotator_abstains_without_evidence() -> None:
    unit = {"unit_id": "AU-NSW:x", "text_sha256": "a" * 64, "text": "No relevant evidence"}
    result = _annotate(unit, role="agent:au-nsw-annotator-b")
    assert result["label"] == "unknown"
    assert result["abstention"] is True


def test_nsw_annotator_roles_have_distinct_observed_rules() -> None:
    unit = {
        "unit_id": "AU-NSW:x",
        "text_sha256": "a" * 64,
        "text": "Government Information (Public Access)",
    }
    assert _annotate(unit, role="agent:au-nsw-annotator-a")["label"] == "observed"
    assert _annotate(unit, role="agent:au-nsw-annotator-b")["label"] == "unknown"
