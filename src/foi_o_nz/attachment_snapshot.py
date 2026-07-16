"""Verification for rights-gated FYI correspondence and attachment snapshots."""

from __future__ import annotations

import json
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AttachmentSnapshotBlocker = Literal[
    "named_human_rights_review_pending",
    "supplemental_attachment_capture_requires_review",
    "human_mapping_review_pending",
    "single_request_only",
]


class AttachmentSnapshotReadiness(BaseModel):
    """Verified evidence and rights state for one attachment-bearing snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["foi-o.fyi-attachment-snapshot-readiness.v0.1.0"] = (
        "foi-o.fyi-attachment-snapshot-readiness.v0.1.0"
    )
    snapshot_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_id: str = Field(min_length=1)
    raw_state_value: str = Field(min_length=1)
    correspondence_count: int = Field(ge=1)
    attachment_count: int = Field(ge=1)
    attachment_bytes: int = Field(ge=1)
    attachment_inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rights_status: Literal["pending", "approved"]
    rights_reviewer: str | None
    rights_reviewed_at: str | None
    storage: Literal["local_only"] = "local_only"
    content_committed: Literal[False] = False
    source_records_modified: Literal[False] = False
    canonical_base_attachment_inventory_empty: Literal[True] = True
    supplemental_attachment_capture_declared: Literal[True] = True
    ready_for_raw_state_mapping_audit: bool
    blockers: tuple[AttachmentSnapshotBlocker, ...]


class _CorrespondenceCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.total = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        classes = set(dict(attrs).get("class", "").split())
        if "correspondence" in classes and "box" in classes:
            self.total += 1


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _validate_rights(rights: dict[str, Any], manifest_digest: str) -> bool:
    if (
        rights.get("schema_version")
        != "foi-o.fyi-attachment-snapshot-rights-review.v0.1.0"
    ):
        raise ValueError("unsupported attachment snapshot rights-review schema version")
    if rights.get("purpose") != "foi-o-raw-state-mapping-audit":
        raise ValueError("snapshot rights purpose mismatch")
    for field in (
        "redistribution_allowed",
        "publication_allowed",
        "training_allowed",
        "fine_tuning_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "reviewed_gold_label_promotion_allowed",
    ):
        if rights.get(field) is not False:
            raise ValueError(f"snapshot rights boundary missing: {field}")
    if rights.get("storage") != "local_only":
        raise ValueError("snapshot must remain local only")
    status = rights.get("status")
    if status == "pending":
        if any(
            rights.get(field) is not None
            for field in ("reviewer", "reviewed_at", "reviewed_snapshot_manifest_sha256")
        ):
            raise ValueError("pending rights review cannot claim approval")
        return False
    if status != "approved":
        raise ValueError("snapshot rights status must be pending or approved")
    if not rights.get("reviewer") or not rights.get("reviewed_at"):
        raise ValueError("approved rights review requires reviewer and reviewed_at")
    reviewed_digest = rights.get("reviewed_snapshot_manifest_sha256")
    if (
        not isinstance(reviewed_digest, str)
        or len(reviewed_digest) != 64
        or any(character not in "0123456789abcdef" for character in reviewed_digest)
        or reviewed_digest == manifest_digest
    ):
        raise ValueError("approved rights review requires the separate reviewed pending digest")
    return True


def verify_attachment_snapshot(
    snapshot_dir: Path,
    *,
    expected_manifest_sha256: str,
    reviewed_snapshot_dir: Path | None = None,
) -> AttachmentSnapshotReadiness:
    """Verify one local attachment snapshot without promoting its rights state."""
    root = snapshot_dir.resolve()
    manifest_path = root / "manifest.json"
    manifest_digest = _digest(manifest_path)
    if manifest_digest != expected_manifest_sha256:
        raise ValueError("snapshot manifest SHA-256 mismatch")
    sidecar_digest = (root / "manifest.sha256").read_text(encoding="utf-8").split()[0]
    if sidecar_digest != manifest_digest:
        raise ValueError("snapshot manifest sidecar mismatch")
    manifest = _load_object(manifest_path)
    if manifest.get("schema_version") != "foi-o.fyi-attachment-evidence-snapshot.v0.1.0":
        raise ValueError("unsupported attachment snapshot schema version")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("snapshot artifacts must be a non-empty list")
    declared: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            raise ValueError("snapshot artifact must declare a path")
        relative = str(artifact["path"])
        if relative in declared:
            raise ValueError("duplicate snapshot artifact path")
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"invalid snapshot artifact path: {relative}")
        if _digest(path) != artifact.get("sha256"):
            raise ValueError(f"artifact SHA-256 mismatch: {relative}")
        if path.stat().st_size != artifact.get("size"):
            raise ValueError(f"artifact size mismatch: {relative}")
        declared[relative] = artifact

    rights = manifest.get("rights_review")
    if not isinstance(rights, dict) or _load_object(root / "rights-review.json") != rights:
        raise ValueError("rights review artifact does not match manifest")
    approved = _validate_rights(rights, manifest_digest)
    if manifest.get("ready_for_raw_state_mapping_audit") is not approved:
        raise ValueError("audit readiness does not match rights review")
    if approved:
        if reviewed_snapshot_dir is None:
            raise ValueError("approved snapshot requires reviewed pending snapshot")
        reviewed_digest = str(rights["reviewed_snapshot_manifest_sha256"])
        reviewed_result = verify_attachment_snapshot(
            reviewed_snapshot_dir,
            expected_manifest_sha256=reviewed_digest,
        )
        if reviewed_result.rights_status != "pending":
            raise ValueError("reviewed snapshot must retain pending rights status")
        reviewed_manifest = _load_object(reviewed_snapshot_dir / "manifest.json")
        reviewed_artifacts = {
            str(artifact["path"]): (str(artifact["sha256"]), int(artifact["size"]))
            for artifact in reviewed_manifest["artifacts"]
            if artifact["path"] != "rights-review.json"
        }
        current_artifacts = {
            relative: (str(artifact["sha256"]), int(artifact["size"]))
            for relative, artifact in declared.items()
            if relative != "rights-review.json"
        }
        if current_artifacts != reviewed_artifacts:
            raise ValueError("approved snapshot content differs from reviewed pending snapshot")
    elif reviewed_snapshot_dir is not None:
        raise ValueError("reviewed snapshot is only valid for approved rights review")

    request = _load_object(root / "content/request.json")
    request_id = str(request.get("id") or "")
    if request_id != str(manifest.get("request_id") or ""):
        raise ValueError("snapshot request identifier mismatch")
    raw_state = request.get("described_state")
    if not isinstance(raw_state, str) or not raw_state:
        raise ValueError("snapshot described_state missing")
    counter = _CorrespondenceCounter()
    counter.feed((root / "content/page.html").read_text(encoding="utf-8"))
    if counter.total == 0:
        raise ValueError("snapshot correspondence evidence missing")

    inventory_path = root / "content/attachments.json"
    inventory = json.loads(inventory_path.read_bytes())
    if not isinstance(inventory, list) or not inventory:
        raise ValueError("snapshot attachment inventory must be non-empty")
    attachment_bytes = 0
    for attachment in inventory:
        if not isinstance(attachment, dict) or not isinstance(attachment.get("path"), str):
            raise ValueError("invalid attachment inventory item")
        relative = str(attachment["path"])
        artifact = declared.get(relative)
        if artifact is None:
            raise ValueError(f"inventory attachment artifact missing: {relative}")
        if (
            attachment.get("sha256") != artifact.get("sha256")
            or attachment.get("size") != artifact.get("size")
        ):
            raise ValueError(f"attachment inventory mismatch: {relative}")
        attachment_bytes += int(artifact["size"])
    supplemental = manifest.get("supplemental_attachment_capture")
    if not isinstance(supplemental, dict):
        raise ValueError("supplemental attachment declaration missing")
    if supplemental.get("attachment_count") != len(inventory):
        raise ValueError("supplemental attachment count mismatch")
    if supplemental.get("attachment_bytes") != attachment_bytes:
        raise ValueError("supplemental attachment byte count mismatch")

    blockers: tuple[AttachmentSnapshotBlocker, ...]
    if approved:
        blockers = ("human_mapping_review_pending", "single_request_only")
    else:
        blockers = (
            "named_human_rights_review_pending",
            "supplemental_attachment_capture_requires_review",
            "human_mapping_review_pending",
            "single_request_only",
        )
    return AttachmentSnapshotReadiness(
        snapshot_manifest_sha256=manifest_digest,
        request_id=request_id,
        raw_state_value=raw_state,
        correspondence_count=counter.total,
        attachment_count=len(inventory),
        attachment_bytes=attachment_bytes,
        attachment_inventory_sha256=_digest(inventory_path),
        rights_status="approved" if approved else "pending",
        rights_reviewer=str(rights["reviewer"]) if approved else None,
        rights_reviewed_at=str(rights["reviewed_at"]) if approved else None,
        ready_for_raw_state_mapping_audit=approved,
        blockers=blockers,
    )
