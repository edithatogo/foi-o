from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.pin_oia_version_hashes import main, pin_hashes

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "mappings/nz-source-rights-registry.yaml"
SCHEMA = ROOT / "schemas/json/source-rights-registry.schema.json"
VERSION_INDEX = ROOT / "mappings/nz-oia-version-index.yaml"


def test_candidate_source_rights_registry_is_schema_valid() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(registry)


def test_registry_is_fail_closed_and_hash_pinned() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert registry["status"] == "candidate"
    assert registry["human_review"]["status"] == "pending"
    assert registry["human_review"]["promotion_allowed"] is False
    entries = {entry["source_id"]: entry for entry in registry["sources"]}

    assert entries["nz-legislation-content"]["redistribution_status"] == "permitted"
    assert entries["nz-ombudsman-content"]["redistribution_status"] == "restricted"
    assert entries["govt-nz-site-content"]["redistribution_status"] == "permitted"
    assert entries["fyi-public-request-content"]["redistribution_status"] == "unknown"
    assert entries["fyi-public-request-content"]["allowed_scope"] == "metadata_only"

    for entry in entries.values():
        assert len(entry["evidence_sha256"]) == 64
        assert entry["review_status"] == "needs_human_review"


def test_registry_does_not_apply_site_terms_to_third_party_request_content() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    entries = {entry["source_id"]: entry for entry in registry["sources"]}
    fyi = entries["fyi-public-request-content"]
    assert "does not state a downstream reuse licence" in fyi["basis"]
    assert fyi["redistribution_status"] == "unknown"
    assert fyi["requires_contact"] is True


def test_oia_historical_version_index_is_complete_and_candidate_only() -> None:
    index = yaml.safe_load(VERSION_INDEX.read_text(encoding="utf-8"))
    assert index["status"] == "candidate"
    assert index["source_listing_sha256"] == (
        "85db4c17da00f85e4e1980b6e00def277b242425525d77e825b1594bdd61eeaa"
    )
    versions = index["versions"]
    assert len(versions) == 50
    assert versions[0]["as_at"] == "1982-12-17"
    assert versions[-1]["as_at"] == "2025-04-05"
    assert [item["as_at"] for item in versions] == sorted(item["as_at"] for item in versions)
    assert len({item["version_id"] for item in versions}) == 50
    assert all(
        isinstance(item["content_sha256"], str) and len(item["content_sha256"]) == 64
        for item in versions
    )
    assert index["human_review"]["promotion_allowed"] is False


def test_pin_hashes_rejects_missing_or_non_pdf_inputs(tmp_path: Path) -> None:
    index = tmp_path / "index.yaml"
    index.write_text(
        '  - {version_id: "1_0", as_at: "2025-01-01", '
        'pdf_url: "https://example.invalid/2025-01-01.pdf", content_sha256: null}\n',
        encoding="utf-8",
    )
    with pytest.raises(FileNotFoundError, match="missing official version PDF"):
        pin_hashes(index, tmp_path)
    (tmp_path / "2025-01-01.pdf").write_bytes(b"not a pdf")
    with pytest.raises(ValueError, match="not a PDF"):
        pin_hashes(index, tmp_path)


def test_pin_hashes_updates_a_valid_pdf_deterministically(tmp_path: Path) -> None:
    index = tmp_path / "index.yaml"
    row = (
        '  - {version_id: "1_0", as_at: "2025-01-01", '
        'pdf_url: "https://example.invalid/2025-01-01.pdf", content_sha256: null}\n'
    )
    index.write_text(row, encoding="utf-8")
    (tmp_path / "2025-01-01.pdf").write_bytes(b"%PDF-1.7\nfixture")
    assert pin_hashes(index, tmp_path) == 1
    first = index.read_text(encoding="utf-8")
    assert "content_sha256: null" not in first
    assert pin_hashes(index, tmp_path) == 1
    assert index.read_text(encoding="utf-8") == first


def test_pin_hashes_rejects_an_index_without_version_rows(tmp_path: Path) -> None:
    index = tmp_path / "index.yaml"
    index.write_text("status: candidate\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no version rows"):
        pin_hashes(index, tmp_path)


def test_pin_hashes_cli_reports_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    index = tmp_path / "index.yaml"
    index.write_text(
        '  - {version_id: "1_0", as_at: "2025-01-01", '
        'pdf_url: "https://example.invalid/2025-01-01.pdf", content_sha256: null}\n',
        encoding="utf-8",
    )
    (tmp_path / "2025-01-01.pdf").write_bytes(b"%PDF-1.7\nfixture")
    monkeypatch.setattr(
        "sys.argv",
        ["pin", "--index", str(index), "--pdf-dir", str(tmp_path)],
    )
    main()
    assert capsys.readouterr().out == "pinned 1 official OIA versions\n"
