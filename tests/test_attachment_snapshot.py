"""Tests for rights-gated FYI correspondence and attachment snapshots."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from foi_o_nz.attachment_snapshot import (
    approve_attachment_snapshot,
    audit_approved_attachment_snapshot,
    verify_attachment_snapshot,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples/v2/fyi-attachment-snapshot-readiness.11872.json"
SCHEMA = ROOT / "schemas/json/fyi-attachment-snapshot-readiness.schema.json"


def _write_manifest(snapshot: Path, manifest: Mapping[str, object]) -> str:
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    (snapshot / "manifest.json").write_bytes(manifest_bytes)
    digest = sha256(manifest_bytes).hexdigest()
    (snapshot / "manifest.sha256").write_text(f"{digest}  manifest.json\n")
    return digest


def _refresh_artifact(snapshot: Path, manifest: dict[str, object], relative: str) -> None:
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list)
    artifacts = cast(list[dict[str, Any]], artifacts)
    artifact = next(item for item in artifacts if item["path"] == relative)
    path = snapshot / relative
    artifact["sha256"] = sha256(path.read_bytes()).hexdigest()
    artifact["size"] = path.stat().st_size


def _write_snapshot(root: Path, *, rights_status: str = "pending") -> tuple[Path, str]:
    snapshot = root / "snapshot"
    (snapshot / "content/attachments").mkdir(parents=True)
    request = {"id": 11872, "described_state": "partially_successful"}
    page = (
        b'<div class="outgoing correspondence box"></div>'
        b'<div class="box correspondence incoming"></div>'
    )
    attachment = b"%PDF-1.7\nfixture"
    inventory = [
        {
            "content_type": "application/pdf",
            "filename": "response.pdf",
            "path": "content/attachments/response.pdf",
            "sha256": sha256(attachment).hexdigest(),
            "size": len(attachment),
            "source_url": "https://fyi.org.nz/request/11872/response/1/attach/1/response.pdf",
        }
    ]
    rights = {
        "schema_version": "foi-o.fyi-attachment-snapshot-rights-review.v0.1.0",
        "status": rights_status,
        "purpose": "foi-o-raw-state-mapping-audit",
        "reviewer": None,
        "reviewed_at": None,
        "reviewed_snapshot_manifest_sha256": None,
        "storage": "local_only",
        "redistribution_allowed": False,
        "publication_allowed": False,
        "training_allowed": False,
        "fine_tuning_allowed": False,
        "release_allowed": False,
        "dataset_publication_allowed": False,
        "reviewed_gold_label_promotion_allowed": False,
    }
    files = {
        "content/request.json": (json.dumps(request) + "\n").encode(),
        "content/page.html": page,
        "content/attachments.json": (json.dumps(inventory) + "\n").encode(),
        "content/attachments/response.pdf": attachment,
        "rights-review.json": (json.dumps(rights) + "\n").encode(),
    }
    artifacts = []
    for relative, content in files.items():
        path = snapshot / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        artifacts.append(
            {"path": relative, "sha256": sha256(content).hexdigest(), "size": len(content)}
        )
    manifest = {
        "schema_version": "foi-o.fyi-attachment-evidence-snapshot.v0.1.0",
        "status": "pending_named_human_rights_review",
        "request_id": "11872",
        "source_url": "https://fyi.org.nz/request/11872",
        "captured_at": "2026-07-16T12:14:40Z",
        "base_capture": {"tool": "fyi-cli", "revision": "a" * 40},
        "supplemental_attachment_capture": {
            "discovery_method": "rendered HTML links",
            "attachment_count": 1,
            "attachment_bytes": len(attachment),
            "reason": "JSON omitted attachment metadata",
        },
        "rights_review": rights,
        "ready_for_raw_state_mapping_audit": False,
        "artifacts": artifacts,
    }
    digest = _write_manifest(snapshot, manifest)
    return snapshot, digest


def test_pending_snapshot_verifies_but_is_not_rights_cleared(tmp_path: Path) -> None:
    snapshot, digest = _write_snapshot(tmp_path)
    result = verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)
    assert result.request_id == "11872"
    assert result.raw_state_value == "partially_successful"
    assert result.correspondence_count == 2
    assert result.attachment_count == 1
    assert result.attachment_bytes > 0
    assert result.rights_status == "pending"
    assert result.ready_for_raw_state_mapping_audit is False


def test_snapshot_rejects_attachment_byte_drift(tmp_path: Path) -> None:
    snapshot, digest = _write_snapshot(tmp_path)
    (snapshot / "content/attachments/response.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="artifact SHA-256 mismatch"):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)


def test_snapshot_rejects_inventory_not_backed_by_artifact(tmp_path: Path) -> None:
    snapshot, digest = _write_snapshot(tmp_path)
    inventory_path = snapshot / "content/attachments.json"
    inventory = json.loads(inventory_path.read_text())
    inventory[0]["path"] = "content/attachments/missing.pdf"
    inventory_path.write_text(json.dumps(inventory))
    manifest = json.loads((snapshot / "manifest.json").read_text())
    _refresh_artifact(snapshot, manifest, "content/attachments.json")
    digest = _write_manifest(snapshot, manifest)
    with pytest.raises(ValueError, match="inventory attachment artifact missing"):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)


def test_approved_snapshot_requires_and_records_named_review(tmp_path: Path) -> None:
    reviewed_snapshot, reviewed_digest = _write_snapshot(tmp_path / "reviewed")
    snapshot = tmp_path / "approved" / "snapshot"
    shutil.copytree(reviewed_snapshot, snapshot)
    manifest = json.loads((snapshot / "manifest.json").read_text())
    rights = manifest["rights_review"]
    rights.update(
        {
            "status": "approved",
            "reviewer": "edithatogo",
            "reviewed_at": "2026-07-16T13:00:00Z",
            "reviewed_snapshot_manifest_sha256": reviewed_digest,
        }
    )
    (snapshot / "rights-review.json").write_text(json.dumps(rights) + "\n")
    manifest["ready_for_raw_state_mapping_audit"] = True
    _refresh_artifact(snapshot, manifest, "rights-review.json")
    digest = _write_manifest(snapshot, manifest)

    result = verify_attachment_snapshot(
        snapshot,
        expected_manifest_sha256=digest,
        reviewed_snapshot_dir=reviewed_snapshot,
    )
    assert result.rights_status == "approved"
    assert result.rights_reviewer == "edithatogo"
    assert result.ready_for_raw_state_mapping_audit is True
    assert result.blockers == ("human_mapping_review_pending", "single_request_only")

    with pytest.raises(ValueError, match="approved snapshot requires reviewed pending snapshot"):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)


def test_approval_copies_reviewed_bytes_and_preserves_restricted_scope(
    tmp_path: Path,
) -> None:
    reviewed_snapshot, reviewed_digest = _write_snapshot(tmp_path / "reviewed")
    approved_snapshot = tmp_path / "approved"

    approved_digest = approve_attachment_snapshot(
        reviewed_snapshot,
        approved_snapshot,
        expected_reviewed_manifest_sha256=reviewed_digest,
        reviewer="edithatogo",
        reviewed_at="2026-07-17T00:00:00Z",
    )

    result = verify_attachment_snapshot(
        approved_snapshot,
        expected_manifest_sha256=approved_digest,
        reviewed_snapshot_dir=reviewed_snapshot,
    )
    assert result.rights_status == "approved"
    assert result.rights_reviewer == "edithatogo"
    rights = json.loads((approved_snapshot / "rights-review.json").read_text())
    assert rights["purpose"] == "foi-o-raw-state-mapping-audit"
    assert all(
        rights[field] is False
        for field in (
            "redistribution_allowed",
            "publication_allowed",
            "training_allowed",
            "fine_tuning_allowed",
            "release_allowed",
            "dataset_publication_allowed",
            "reviewed_gold_label_promotion_allowed",
        )
    )


def test_approved_attachment_snapshot_produces_bounded_mapping_audit(
    tmp_path: Path,
) -> None:
    reviewed_snapshot, reviewed_digest = _write_snapshot(tmp_path / "reviewed")
    approved_snapshot = tmp_path / "approved"
    approved_digest = approve_attachment_snapshot(
        reviewed_snapshot,
        approved_snapshot,
        expected_reviewed_manifest_sha256=reviewed_digest,
        reviewer="edithatogo",
        reviewed_at="2026-07-17T00:00:00Z",
    )

    result = audit_approved_attachment_snapshot(
        approved_snapshot,
        reviewed_snapshot_dir=reviewed_snapshot,
        mapping_path=ROOT / "mappings/alaveteli-state-map.yaml",
        expected_manifest_sha256=approved_digest,
    )

    assert result.request_id == "11872"
    assert result.raw_state_value == "partially_successful"
    assert result.normalised_state == "released_in_part"
    assert result.correspondence_count == 2
    assert result.attachment_count == 1
    assert result.nonempty_attachment_evidence is True
    assert result.rights_purpose == "foi-o-raw-state-mapping-audit"
    assert result.promotion_allowed is False
    assert result.blockers == ("human_mapping_review_pending", "single_request_only")


def test_approved_snapshot_rejects_content_different_from_reviewed_pending(
    tmp_path: Path,
) -> None:
    reviewed_snapshot, reviewed_digest = _write_snapshot(tmp_path / "reviewed")
    snapshot = tmp_path / "approved" / "snapshot"
    shutil.copytree(reviewed_snapshot, snapshot)
    manifest = json.loads((snapshot / "manifest.json").read_text())
    rights = manifest["rights_review"]
    rights.update(
        {
            "status": "approved",
            "reviewer": "edithatogo",
            "reviewed_at": "2026-07-16T13:00:00Z",
            "reviewed_snapshot_manifest_sha256": reviewed_digest,
        }
    )
    (snapshot / "rights-review.json").write_text(json.dumps(rights) + "\n")
    manifest["ready_for_raw_state_mapping_audit"] = True
    (snapshot / "content/attachments/response.pdf").write_bytes(b"%PDF-different")
    _refresh_artifact(snapshot, manifest, "content/attachments/response.pdf")
    inventory_path = snapshot / "content/attachments.json"
    inventory = json.loads(inventory_path.read_text())
    artifact = next(
        item for item in manifest["artifacts"] if item["path"] == "content/attachments/response.pdf"
    )
    inventory[0]["sha256"] = artifact["sha256"]
    inventory[0]["size"] = artifact["size"]
    inventory_path.write_text(json.dumps(inventory) + "\n")
    _refresh_artifact(snapshot, manifest, "content/attachments.json")
    manifest["supplemental_attachment_capture"]["attachment_bytes"] = artifact["size"]
    _refresh_artifact(snapshot, manifest, "rights-review.json")
    digest = _write_manifest(snapshot, manifest)

    with pytest.raises(ValueError, match="approved snapshot content differs"):
        verify_attachment_snapshot(
            snapshot,
            expected_manifest_sha256=digest,
            reviewed_snapshot_dir=reviewed_snapshot,
        )


def test_snapshot_rejects_manifest_and_sidecar_mismatches(tmp_path: Path) -> None:
    snapshot, digest = _write_snapshot(tmp_path)
    with pytest.raises(ValueError, match="snapshot manifest SHA-256 mismatch"):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256="0" * 64)
    (snapshot / "manifest.sha256").write_text(f"{'1' * 64}  manifest.json\n")
    with pytest.raises(ValueError, match="snapshot manifest sidecar mismatch"):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("schema", "unsupported attachment snapshot schema version"),
        ("rights_schema", "unsupported attachment snapshot rights-review schema version"),
        ("rights_boundary", "snapshot rights boundary missing"),
        ("rights_storage", "snapshot must remain local only"),
        ("pending_claim", "pending rights review cannot claim approval"),
        ("audit_readiness", "audit readiness does not match rights review"),
        ("supplemental_count", "supplemental attachment count mismatch"),
        ("supplemental_bytes", "supplemental attachment byte count mismatch"),
    ],
)
def test_snapshot_rejects_fail_closed_manifest_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    snapshot, _ = _write_snapshot(tmp_path)
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if mutation == "schema":
        manifest["schema_version"] = "unknown"
    elif mutation == "rights_schema":
        manifest["rights_review"]["schema_version"] = "unknown"
        (snapshot / "rights-review.json").write_text(json.dumps(manifest["rights_review"]) + "\n")
        _refresh_artifact(snapshot, manifest, "rights-review.json")
    elif mutation == "rights_boundary":
        manifest["rights_review"]["publication_allowed"] = True
        (snapshot / "rights-review.json").write_text(json.dumps(manifest["rights_review"]) + "\n")
        _refresh_artifact(snapshot, manifest, "rights-review.json")
    elif mutation == "rights_storage":
        manifest["rights_review"]["storage"] = "remote"
        (snapshot / "rights-review.json").write_text(json.dumps(manifest["rights_review"]) + "\n")
        _refresh_artifact(snapshot, manifest, "rights-review.json")
    elif mutation == "pending_claim":
        manifest["rights_review"]["reviewer"] = "invented"
        (snapshot / "rights-review.json").write_text(json.dumps(manifest["rights_review"]) + "\n")
        _refresh_artifact(snapshot, manifest, "rights-review.json")
    elif mutation == "audit_readiness":
        manifest["ready_for_raw_state_mapping_audit"] = True
    elif mutation == "supplemental_count":
        manifest["supplemental_attachment_capture"]["attachment_count"] = 2
    else:
        manifest["supplemental_attachment_capture"]["attachment_bytes"] = 1
    digest = _write_manifest(snapshot, manifest)
    with pytest.raises(ValueError, match=message):
        verify_attachment_snapshot(snapshot, expected_manifest_sha256=digest)


def test_committed_approved_readiness_is_schema_valid() -> None:
    result = validate_json_schema(EXAMPLE, SCHEMA)
    assert not result.errors, result.errors
    payload = json.loads(EXAMPLE.read_text())
    assert payload["snapshot_manifest_sha256"] == (
        "0c7cee553ca3b01a6416784a1b691df5a6d90159a8f4d55e51a799934f655629"
    )
    assert payload["correspondence_count"] == 4
    assert payload["attachment_count"] == 3
    assert payload["rights_status"] == "approved"
    assert payload["rights_reviewer"] == "edithatogo"
    assert payload["ready_for_raw_state_mapping_audit"] is True
