"""Tests for the rights-cleared bounded raw-state audit."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.bounded_raw_state_audit import audit_bounded_raw_state
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
EXAMPLES = (
    ROOT / "examples/v2/bounded-raw-state-audit.35076.json",
    ROOT / "examples/v2/bounded-raw-state-audit.11872.json",
)
SCHEMA = ROOT / "schemas/json/bounded-raw-state-audit.schema.json"
REVIEW = ROOT / "examples/v2/bounded-raw-state-mapping-review.11872.json"
REVIEW_SCHEMA = ROOT / "schemas/json/bounded-raw-state-mapping-review.schema.json"


def _write_snapshot(root: Path, *, attachments: list[object] | None = None) -> Path:
    snapshot = root / "snapshot"
    (snapshot / "content").mkdir(parents=True)
    request = {"id": 35076, "described_state": "waiting_response"}
    page = '<div class="outgoing correspondence box" id="outgoing-1"></div>'
    attachment_values = attachments or []
    files = {
        "content/request.json": json.dumps(request).encode(),
        "content/page.html": page.encode(),
        "content/attachments.json": json.dumps(attachment_values).encode(),
    }
    artifacts = []
    for relative, content in files.items():
        path = snapshot / relative
        path.write_bytes(content)
        artifacts.append(
            {"path": relative, "sha256": sha256(content).hexdigest(), "size": len(content)}
        )
    manifest = {
        "artifacts": artifacts,
        "rights_review": {
            "status": "approved",
            "purpose": "foi-o-candidate-extraction",
            "redistribution_allowed": False,
            "reviewer": "edithatogo",
            "reviewed_at": "2026-07-16T10:40:17Z",
        },
        "requests": [{"request_id": "35076"}],
    }
    (snapshot / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return snapshot


def test_bounded_audit_verifies_correspondence_and_empty_attachment_inventory(
    tmp_path: Path,
) -> None:
    snapshot = _write_snapshot(tmp_path)
    manifest = snapshot / "manifest.json"
    before = {path: path.read_bytes() for path in snapshot.rglob("*") if path.is_file()}
    report = audit_bounded_raw_state(
        snapshot,
        mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
        expected_manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),
    )

    assert report.raw_state_value == "waiting_response"
    assert report.normalised_state == "awaiting_response"
    assert report.correspondence_count == 1
    assert report.outgoing_correspondence_count == 1
    assert report.incoming_correspondence_count == 0
    assert report.attachment_count == 0
    assert report.attachment_inventory_verified is True
    assert report.nonempty_attachment_evidence is False
    assert report.ready_for_bounded_human_mapping_review is True
    assert report.ready_for_archive_wide_mapping_claim is False
    assert report.blockers == (
        "human_mapping_review_pending",
        "no_nonempty_attachment_evidence",
        "single_request_only",
    )
    assert before == {path: path.read_bytes() for path in snapshot.rglob("*") if path.is_file()}


def test_bounded_audit_records_nonempty_attachment_evidence(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path, attachments=[{"id": "attachment-1"}])
    report = audit_bounded_raw_state(
        snapshot,
        mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
        expected_manifest_sha256=sha256((snapshot / "manifest.json").read_bytes()).hexdigest(),
    )
    assert report.attachment_count == 1
    assert report.nonempty_attachment_evidence is True
    assert report.blockers == ("human_mapping_review_pending", "single_request_only")


def test_bounded_audit_rejects_rights_or_artifact_drift(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path)
    manifest = snapshot / "manifest.json"
    digest = sha256(manifest.read_bytes()).hexdigest()
    (snapshot / "content/page.html").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="snapshot artifact drift"):
        audit_bounded_raw_state(
            snapshot,
            mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
            expected_manifest_sha256=digest,
        )


def test_committed_bounded_audit_is_schema_valid() -> None:
    for example in EXAMPLES:
        result = validate_json_schema(example, SCHEMA)
        assert not result.errors, result.errors
    report = json.loads(EXAMPLES[0].read_text())
    assert report["request_id"] == "35076"
    assert report["correspondence_count"] == 1
    assert report["attachment_count"] == 0
    assert report["ready_for_bounded_human_mapping_review"] is True
    assert report["ready_for_archive_wide_mapping_claim"] is False


def test_schema_rejects_attachment_and_blocker_contradiction(tmp_path: Path) -> None:
    payload = json.loads(EXAMPLES[0].read_text())
    payload["blockers"].remove("no_nonempty_attachment_evidence")
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_json_schema(path, SCHEMA)
    assert result.errors


def test_committed_bounded_mapping_review_is_exact_and_fail_closed() -> None:
    result = validate_json_schema(REVIEW, REVIEW_SCHEMA)
    assert not result.errors, result.errors
    review = json.loads(REVIEW.read_text())
    assert review["reviewer"] == "edithatogo"
    assert review["request_id"] == "11872"
    assert review["candidate_mapping"] == {
        "raw_state": "partially_successful",
        "normalised_state": "released_in_part",
    }
    audit_path = ROOT / review["audit_artifact_path"]
    assert review["audit_artifact_sha256"] == sha256(audit_path.read_bytes()).hexdigest()
    assert review["scope"] == "bounded_request_only"
    assert review["archive_wide_claim_allowed"] is False
    assert all(value is False for value in review["prohibited_actions"].values())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("archive_wide_claim_allowed", True),
        ("publication", True),
        ("legal_certification", True),
        ("reviewed_gold_label_promotion", True),
    ],
)
def test_bounded_mapping_review_rejects_scope_expansion(
    tmp_path: Path, field: str, value: bool
) -> None:
    review = json.loads(REVIEW.read_text())
    if field == "archive_wide_claim_allowed":
        review[field] = value
    else:
        review["prohibited_actions"][field] = value
    invalid = tmp_path / "mapping-review.json"
    invalid.write_text(json.dumps(review), encoding="utf-8")
    result = validate_json_schema(invalid, REVIEW_SCHEMA)
    assert result.errors
