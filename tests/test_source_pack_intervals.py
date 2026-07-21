"""Tests for deterministic candidate OIA applicability intervals."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path

import jsonschema
import pytest
import yaml

from foi_o_nz.source_pack_intervals import build_oia_interval_candidates

ROOT = Path(__file__).parents[1]
INDEX = ROOT / "mappings/nz-oia-version-index.yaml"
OUTPUT = ROOT / "mappings/nz-oia-applicability-interval-candidates.yaml"
SCHEMA = ROOT / "schemas/json/nz-oia-applicability-interval-candidates.schema.json"


def test_committed_candidate_intervals_are_deterministic_and_complete() -> None:
    expected = build_oia_interval_candidates(INDEX).model_dump(mode="json")
    actual = yaml.safe_load(OUTPUT.read_text())
    assert actual == expected
    assert actual["source_index_sha256"] == sha256(INDEX.read_bytes()).hexdigest()
    assert actual["interval_count"] == 50
    assert actual["intervals"][0] == {
        "version_id": "0_1",
        "valid_from_inclusive": "1982-12-17",
        "valid_to_exclusive": "2007-09-03",
        "derivation": "adjacent_official_as_at_dates",
        "legal_applicability_approved": False,
    }
    assert actual["intervals"][-1]["valid_to_exclusive"] is None
    jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text())).validate(actual)


def test_every_interval_is_adjacent_and_unapproved() -> None:
    artifact = build_oia_interval_candidates(INDEX)
    for current, following in zip(artifact.intervals, artifact.intervals[1:], strict=False):
        assert current.valid_to_exclusive == following.valid_from_inclusive
        assert current.legal_applicability_approved is False
    assert artifact.legal_applicability_approved is False
    assert artifact.source_pack_promotion_allowed is False


def test_unsorted_or_duplicate_dates_fail_closed(tmp_path: Path) -> None:
    payload = yaml.safe_load(INDEX.read_text())
    payload["versions"][1]["as_at"] = payload["versions"][0]["as_at"]
    path = tmp_path / "index.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=r"strictly ordered|unique"):
        build_oia_interval_candidates(path)


def test_candidate_dates_are_document_selection_not_legal_findings() -> None:
    artifact = build_oia_interval_candidates(INDEX)
    assert artifact.intervals[0].valid_from_inclusive == date(1982, 12, 17)
    assert "as-at adjacency alone is not legal applicability" in artifact.required_review
