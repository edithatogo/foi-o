"""Fail-closed tests for governed re-extraction input auditing."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.reextraction import audit_reextraction_input
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas" / "json" / "reextraction-input-audit.schema.json"
REPORT = ROOT / "examples" / "v2" / "reextraction-input-audit.fc27.json"
REVISION = "fc27bfa471c598a31d975cfa2b603b1a11408e55"


def _write_manifest(path: Path, requests: list[dict[str, object]]) -> str:
    path.write_text(
        json.dumps(
            {
                "meta": {
                    "record_count": len(requests),
                    "generated_at": "2026-07-13T01:57:41Z",
                    "version": "0.10.3",
                },
                "requests": requests,
            }
        ),
        encoding="utf-8",
    )
    return sha256(path.read_bytes()).hexdigest()


def _request(request_id: int, *, license_value: str | None = "CC-BY-4.0") -> dict[str, object]:
    return {
        "request_id": request_id,
        "content_sha256": f"{request_id:064x}",
        "license": license_value,
    }


def test_complete_rights_and_integrity_input_is_ready(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    digest = _write_manifest(manifest, [_request(1), _request(2)])
    report = audit_reextraction_input(
        manifest,
        dataset_repository="edithatogo/fyi-archive-nz",
        dataset_revision=REVISION,
        configuration="default",
        split="requests",
        expected_manifest_sha256=digest,
    )
    assert report.ready_for_reextraction is True
    assert report.blockers == []
    assert report.source_records_modified is False


def test_null_rights_missing_digest_and_duplicates_fail_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    records = [_request(1, license_value=None), _request(1)]
    records[1]["content_sha256"] = "not-a-digest"
    digest = _write_manifest(manifest, records)
    report = audit_reextraction_input(
        manifest,
        dataset_repository="edithatogo/fyi-archive-nz",
        dataset_revision=REVISION,
        configuration="default",
        split="requests",
        expected_manifest_sha256=digest,
    )
    assert report.ready_for_reextraction is False
    assert report.records_without_declared_license == 1
    assert report.records_with_invalid_content_sha256 == 1
    assert report.duplicate_request_ids == ["1"]
    assert report.blockers == [
        "duplicate_request_ids",
        "invalid_content_sha256",
        "missing_declared_license",
    ]


def test_manifest_digest_mismatch_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_request(1)])
    with pytest.raises(ValueError, match="manifest SHA-256"):
        audit_reextraction_input(
            manifest,
            dataset_repository="edithatogo/fyi-archive-nz",
            dataset_revision=REVISION,
            configuration="default",
            split="requests",
            expected_manifest_sha256="0" * 64,
        )


def test_committed_fc27_report_is_schema_valid_and_blocked_on_rights() -> None:
    result = validate_json_schema(REPORT, SCHEMA)
    assert not result.errors, result.errors
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["dataset_revision"] == REVISION
    assert report["manifest_sha256"] == (
        "23cab9ee0ac6986326d67c91a91e415456a1d0589c90ec1c1628556e0d0d6e1e"
    )
    assert report["record_count"] == 33217
    assert report["records_with_valid_content_sha256"] == 33217
    assert report["records_without_declared_license"] == 33217
    assert report["ready_for_reextraction"] is False
    assert report["blockers"] == ["missing_declared_license"]
