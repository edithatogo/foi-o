import hashlib
import json
from pathlib import Path

from scripts.validate_australian_source_artifact import validate_artifact


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    records = tmp_path / "records.jsonl"
    records.write_text(
        json.dumps({
            "jurisdiction": "AU-CTH",
            "source_url": "https://example.test/request/1",
            "text": "Authentic source text",
        })
        + "\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({
        "schema_version": "foi-o.australian-source-artifact.v0.1.0",
        "artifact_id": "test-cth-1",
        "status": "authentic_frozen_candidate",
        "jurisdiction": "AU-CTH",
        "regime": "FOI",
        "source_url": "https://example.test",
        "retrieved_at": "2026-07-22T00:00:00Z",
        "rights_review_status": "approved",
        "records_path": "records.jsonl",
        "records_sha256": hashlib.sha256(records.read_bytes()).hexdigest(),
        "byte_count": records.stat().st_size,
        "record_count": 1,
    }), encoding="utf-8")
    return artifact, records


def test_valid_authentic_artifact_passes(tmp_path: Path) -> None:
    artifact, _ = _write_fixture(tmp_path)
    assert validate_artifact(artifact, tmp_path) == []


def test_tampered_records_and_candidate_leak_fail_closed(tmp_path: Path) -> None:
    artifact, records = _write_fixture(tmp_path)
    records.write_text(
        json.dumps({
            "jurisdiction": "AU-CTH",
            "source_url": "https://example.test/request/1",
            "text": "changed",
            "candidate_label": "successful",
        })
        + "\n",
        encoding="utf-8",
    )
    errors = validate_artifact(artifact, tmp_path)
    assert "records_sha256 does not match records file" in errors
    assert "record 1 contains extractor/candidate output" in errors


def test_rights_and_regime_mismatch_fail_closed(tmp_path: Path) -> None:
    artifact, _ = _write_fixture(tmp_path)
    value = json.loads(artifact.read_text(encoding="utf-8"))
    value["jurisdiction"] = "AU-NSW"
    value["rights_review_status"] = "pending"
    artifact.write_text(json.dumps(value), encoding="utf-8")
    errors = validate_artifact(artifact, tmp_path)
    assert "regime does not match jurisdiction" in errors
    assert "rights review is not approved" in errors
