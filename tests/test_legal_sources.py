from __future__ import annotations

from pathlib import Path

from foi_o_nz.legal_sources import (
    build_legal_source_status,
    load_legal_source_mapping,
    validate_legal_source_mapping,
)

MAPPING_PATH = Path("mappings/nz-legislation-sources.yaml")


def test_legal_source_mapping_records_versions_and_status() -> None:
    report = validate_legal_source_mapping(MAPPING_PATH)
    mapping = load_legal_source_mapping(MAPPING_PATH)

    assert report["ok"] is True, report["errors"]
    assert report["source_count"] >= 3
    assert report["reference_count"] >= 5
    assert "nz.oia.act" in mapping["sources"]
    assert "nz.ombudsman.oia-guide" in mapping["sources"]
    oia_source = mapping["sources"]["nz.oia.act"]
    assert oia_source["work_id"] == "act_public_1982_156"
    assert oia_source["source_status"] == "official_snapshot"
    assert oia_source["retrieved_at"] == "2026-07-02T00:00:00Z"
    assert oia_source["version_id"].startswith("legislation.govt.nz:")


def test_key_legal_references_are_source_versioned() -> None:
    mapping = load_legal_source_mapping(MAPPING_PATH)
    required = {
        "source_id",
        "reference",
        "concept",
        "uri",
        "work_id",
        "version_id",
        "retrieved_at",
        "source_status",
        "applicability_basis",
    }

    for reference in mapping["key_references_initial"]:
        assert required <= set(reference), reference
        assert reference["applicability_basis"] in {
            "current_at_event_time",
            "current_at_extraction_time",
            "unknown",
        }


def test_live_source_status_fails_closed_without_cache(tmp_path: Path) -> None:
    report = build_legal_source_status(
        mapping_path=MAPPING_PATH,
        live=True,
        cache_dir=tmp_path / "missing-live-cache",
    )

    assert report["ok"] is False
    assert report["mapping_ok"] is True
    assert report["live_source_status"] == "external_gate"
    assert report["cache_dir"] == str(tmp_path / "missing-live-cache")
    assert any("live_source_unavailable" in item for item in report["warnings"])
