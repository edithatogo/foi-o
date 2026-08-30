import json
import sys
from pathlib import Path

from scripts.validate_australian_cdx_candidate import HEADER, main, validate_candidate

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/australian-cdx-candidate-manifest.schema.json"


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    unpacked = tmp_path / "unpacked"
    pages = unpacked / "internet_archive_all_captures_cdx.pages"
    pages.mkdir(parents=True)
    records = [
        HEADER,
        [
            "https://www.righttoknow.org.au/request/example",
            "20200101000000",
            "ABC",
            "200",
            "100",
        ],
    ]
    cdx = unpacked / "internet_archive_all_captures_cdx.json"
    cdx.write_text(json.dumps(records))
    import hashlib

    cdx_sha = hashlib.sha256(cdx.read_bytes()).hexdigest()
    retrieval = {
        "pagination_complete": True,
        "retrieval_status": "complete",
        "eligible_for_empirical_freeze": False,
        "publication": False,
        "redistribution": False,
        "record_count": 1,
        "response_sha256": cdx_sha,
        "checkpoint": {"page_count": 1},
    }
    retrieval_path = unpacked / "retrieval.json"
    retrieval_path.write_text(json.dumps(retrieval))
    (pages / "page-000000.json").write_text(
        json.dumps({"page": 0, "header": HEADER, "rows": records[1:]})
    )
    (pages / "checkpoint.json").write_text(json.dumps({"record_count": 1}))
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"fixture")

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    packet = {
        "schema_version": "foi-o.australian-cdx-candidate-manifest.v0.1.0",
        "packet_id": "fixture",
        "status": "candidate_pending_manifest_finalization",
        "source": {
            "provider": "Internet Archive CDX",
            "repository": "edithatogo/fyi-archive",
            "workflow_run_id": "1",
            "artifact_name": "fixture",
            "artifact_id": "1",
            "url_scope": "https://www.righttoknow.org.au/request/*",
            "retrieved_at": "2026-07-27T04:03:29Z",
        },
        "integrity": {
            "artifact_sha256": digest(artifact),
            "cdx_sha256": digest(cdx),
            "retrieval_evidence_sha256": digest(retrieval_path),
            "verified": True,
        },
        "coverage": {
            "pagination_complete": True,
            "page_count": 1,
            "record_count": 1,
            "unique_original_urls": 1,
            "unique_capture_keys": 1,
            "duplicate_capture_rows": 0,
            "scope_conforming_records": 1,
        },
        "metadata_only_classification": {
            "method": "explicit_authority_metadata_only",
            "AU-CTH": 0,
            "AU-NSW": 0,
            "unresolved": 1,
            "classification_complete": False,
            "reason": "CDX has no authority metadata.",
        },
        "rights_boundary": {
            "publication": False,
            "redistribution": False,
            "empirical_freeze": False,
            "reference_sha256": digest(retrieval_path),
        },
        "authorization": {
            "approved_operations": ["validation", "classification", "candidate_packet"],
            "prohibited_operations": ["replay"],
        },
    }
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet))
    return packet_path, artifact, unpacked


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value))


def _rehash(packet_path: Path, artifact: Path, unpacked: Path) -> None:
    import hashlib

    packet = _json(packet_path)
    paths = {
        "artifact_sha256": artifact,
        "cdx_sha256": unpacked / "internet_archive_all_captures_cdx.json",
        "retrieval_evidence_sha256": unpacked / "retrieval.json",
    }
    for field, path in paths.items():
        packet["integrity"][field] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_json(packet_path, packet)


def test_valid_candidate_passes(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    errors, stats = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert errors == []
    assert stats["record_count"] == 1


def test_candidate_rejects_jurisdiction_inference(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    value = json.loads(packet.read_text())
    value["metadata_only_classification"]["AU-CTH"] = 1
    value["metadata_only_classification"]["unresolved"] = 0
    packet.write_text(json.dumps(value))
    errors, _ = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert "CDX-only records cannot be jurisdiction-resolved without authority metadata" in errors


def test_candidate_rejects_missing_file_and_invalid_schema(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    value = _json(packet)
    value["status"] = "final"
    _write_json(packet, value)
    (unpacked / "retrieval.json").unlink()
    errors, stats = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert any(error.startswith("packet schema:") for error in errors)
    assert any(error.startswith("missing required file:") for error in errors)
    assert stats == {}


def test_candidate_rejects_hash_and_header_drift(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    artifact.write_bytes(b"changed")
    cdx = unpacked / "internet_archive_all_captures_cdx.json"
    _write_json(cdx, [["wrong"]])
    errors, stats = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert "artifact_sha256 mismatch" in errors
    assert "cdx_sha256 mismatch" in errors
    assert "CDX header does not match the approved export contract" in errors
    assert stats == {}


def test_candidate_rejects_malformed_page_row_scope_and_counts(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    cdx = unpacked / "internet_archive_all_captures_cdx.json"
    _write_json(
        cdx,
        [
            HEADER,
            ["https://example.test/request/outside", "1", "A", "200", "1"],
            ["malformed"],
        ],
    )
    page = unpacked / "internet_archive_all_captures_cdx.pages/page-000000.json"
    _write_json(page, {"page": 2, "header": ["wrong"], "rows": []})
    checkpoint = unpacked / "internet_archive_all_captures_cdx.pages/checkpoint.json"
    _write_json(checkpoint, {"record_count": 99})
    retrieval = unpacked / "retrieval.json"
    value = _json(retrieval)
    value["record_count"] = 99
    value["checkpoint"]["page_count"] = 2
    _write_json(retrieval, value)
    _rehash(packet, artifact, unpacked)
    errors, stats = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert "page-000000.json has an invalid header" in errors
    assert "CDX row 3 is malformed" in errors
    assert "consolidated, paged, and declared record counts differ" in errors
    assert "checkpoint record count differs" in errors
    assert "page count differs from retrieval evidence" in errors
    assert "one or more CDX records fall outside the approved URL scope" in errors
    assert any(error.startswith("coverage.") for error in errors)
    assert stats["scope_conforming_records"] == 0


def test_candidate_rejects_retrieval_and_classification_drift(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    retrieval = unpacked / "retrieval.json"
    value = _json(retrieval)
    value.update({
        "pagination_complete": False,
        "retrieval_status": "partial",
        "eligible_for_empirical_freeze": True,
        "publication": True,
        "redistribution": True,
        "response_sha256": "0" * 64,
    })
    _write_json(retrieval, value)
    _rehash(packet, artifact, unpacked)
    value = _json(packet)
    value["metadata_only_classification"]["unresolved"] = 0
    _write_json(packet, value)
    errors, _ = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert "retrieval pagination is not complete" in errors
    assert "retrieval status is not complete" in errors
    assert "retrieval must remain ineligible for empirical freeze" in errors
    assert "retrieval rights boundary is not fail-closed" in errors
    assert "retrieval response_sha256 does not match CDX" in errors
    assert "classification counts do not cover every record" in errors
    assert "all CDX-only records must remain unresolved" in errors


def test_candidate_rejects_noncontiguous_pages(tmp_path: Path) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    pages = unpacked / "internet_archive_all_captures_cdx.pages"
    (pages / "page-000000.json").rename(pages / "page-000001.json")
    errors, _ = validate_candidate(packet, SCHEMA, artifact, unpacked)
    assert "CDX page sequence is not contiguous" in errors


def test_main_reports_pass_and_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    packet, artifact, unpacked = _write_fixture(tmp_path)
    args = [
        "validate",
        str(packet),
        "--schema",
        str(SCHEMA),
        "--artifact-zip",
        str(artifact),
        "--unpacked-root",
        str(unpacked),
    ]
    monkeypatch.setattr(sys, "argv", args)
    assert main() == 0
    assert "Australian CDX candidate: PASS" in capsys.readouterr().out

    artifact.write_bytes(b"changed")
    assert main() == 1
    assert "ERROR: artifact_sha256 mismatch" in capsys.readouterr().out
