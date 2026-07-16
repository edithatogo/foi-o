import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.raw_state_audit import audit_raw_state_inputs
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REVISION = "fc27bfa471c598a31d975cfa2b603b1a11408e55"


def _write_manifest(path: Path, requests: list[dict[str, object]]) -> str:
    path.write_text(
        json.dumps({"meta": {"record_count": len(requests)}, "requests": requests}),
        encoding="utf-8",
    )
    return sha256(path.read_bytes()).hexdigest()


def test_audit_reports_evidence_coverage_without_modifying_input(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest,
        [
            {
                "request_id": 1,
                "state": "successful",
                "correspondence": [{"id": "message.1"}],
                "attachments": [{"id": "attachment.1"}],
            },
            {"request_id": 2, "state": "dry-run", "attachments": []},
            {"request_id": 3, "state": "", "attachments": []},
        ],
    )
    before = manifest.read_bytes()

    report = audit_raw_state_inputs(
        manifest,
        mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
        dataset_revision=REVISION,
        expected_manifest_sha256=digest,
    )

    assert manifest.read_bytes() == before
    assert report.observed_state_counts == {"": 1, "dry-run": 1, "successful": 1}
    assert report.records_with_mapped_state == 1
    assert report.unmapped_nonempty_states == ["dry-run"]
    assert report.records_with_correspondence == 1
    assert report.records_with_nonempty_attachments == 1
    assert report.ready_for_mapping_audit is False
    assert report.blockers == ["missing_state_values", "unmapped_source_states"]
    assert report.source_records_modified is False


def test_no_correspondence_or_attachments_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest,
        [{"request_id": 1, "state": "successful", "attachments": []}],
    )
    report = audit_raw_state_inputs(
        manifest,
        mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
        dataset_revision=REVISION,
        expected_manifest_sha256=digest,
    )
    assert report.blockers == ["no_correspondence_evidence", "no_attachment_evidence"]
    assert report.ready_for_mapping_audit is False


def test_manifest_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [])
    with pytest.raises(ValueError, match="manifest SHA-256"):
        audit_raw_state_inputs(
            manifest,
            mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
            dataset_revision=REVISION,
            expected_manifest_sha256="0" * 64,
        )


def test_committed_fc27_readiness_report_is_schema_valid() -> None:
    report_path = ROOT / "examples/v2/raw-state-audit-readiness.fc27.json"
    schema_path = ROOT / "schemas/json/raw-state-audit-readiness.schema.json"
    result = validate_json_schema(report_path, schema_path)
    assert not result.errors, result.errors
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["record_count"] == 33217
    assert report["observed_state_counts"] == {"": 33208, "dry-run": 9}
    assert report["records_with_correspondence"] == 0
    assert report["records_with_nonempty_attachments"] == 0
    assert report["records_with_mapped_state"] == 0
    assert report["ready_for_mapping_audit"] is False
    assert report["blockers"] == [
        "missing_state_values",
        "unmapped_source_states",
        "no_correspondence_evidence",
        "no_attachment_evidence",
    ]
