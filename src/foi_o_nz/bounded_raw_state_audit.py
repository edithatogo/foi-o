"""Bounded correspondence-backed raw-state audit for approved FYI snapshots."""

from __future__ import annotations

import json
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

BoundedAuditBlocker = Literal[
    "human_mapping_review_pending",
    "no_nonempty_attachment_evidence",
    "single_request_only",
]


class BoundedRawStateAudit(BaseModel):
    """One-request state audit that preserves evidence and promotion boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["foi-o.bounded-raw-state-audit.v0.1.0"] = (
        "foi-o.bounded-raw-state-audit.v0.1.0"
    )
    request_id: str = Field(min_length=1)
    snapshot_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_json_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_html_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    attachment_inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rights_reviewer: str = Field(min_length=1)
    rights_reviewed_at: str = Field(min_length=1)
    rights_purpose: Literal["foi-o-candidate-extraction", "foi-o-raw-state-mapping-audit"]
    storage: Literal["local_only"] = "local_only"
    raw_state_field: Literal["described_state"] = "described_state"
    raw_state_value: str = Field(min_length=1)
    normalised_state: str = Field(min_length=1)
    correspondence_count: int = Field(ge=1)
    outgoing_correspondence_count: int = Field(ge=0)
    incoming_correspondence_count: int = Field(ge=0)
    attachment_count: int = Field(ge=0)
    correspondence_evidence_verified: Literal[True] = True
    attachment_inventory_verified: Literal[True] = True
    nonempty_attachment_evidence: bool
    candidate_mapping_supported: Literal[True] = True
    ready_for_bounded_human_mapping_review: Literal[True] = True
    ready_for_archive_wide_mapping_claim: Literal[False] = False
    human_mapping_review_required: Literal[True] = True
    promotion_allowed: Literal[False] = False
    source_records_modified: Literal[False] = False
    blockers: tuple[BoundedAuditBlocker, ...]


class _CorrespondenceCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.total = 0
        self.incoming = 0
        self.outgoing = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        classes = set(dict(attrs).get("class", "").split())
        if "correspondence" not in classes or "box" not in classes:
            return
        self.total += 1
        self.incoming += int("incoming" in classes)
        self.outgoing += int("outgoing" in classes)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def audit_bounded_raw_state(
    snapshot_dir: Path,
    *,
    mapping_path: Path,
    expected_manifest_sha256: str,
) -> BoundedRawStateAudit:
    """Audit one rights-approved snapshot without extracting correspondence text."""
    manifest_path = snapshot_dir / "manifest.json"
    manifest_sha256 = _digest(manifest_path)
    if manifest_sha256 != expected_manifest_sha256:
        raise ValueError("snapshot manifest SHA-256 mismatch")
    manifest = _load_object(manifest_path)
    rights = manifest.get("rights_review")
    if not isinstance(rights, dict) or rights.get("status") != "approved":
        raise ValueError("snapshot rights review is not approved")
    if rights.get("purpose") != "foi-o-candidate-extraction":
        raise ValueError("snapshot rights purpose mismatch")
    if rights.get("redistribution_allowed") is not False:
        raise ValueError("snapshot redistribution boundary missing")
    requests = manifest.get("requests")
    if not isinstance(requests, list) or len(requests) != 1:
        raise ValueError("bounded audit requires exactly one request")
    request_entry = requests[0]
    if not isinstance(request_entry, dict):
        raise ValueError("snapshot request must be an object")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("snapshot artifacts must be a list")
    declared = {
        artifact.get("path"): artifact
        for artifact in artifacts
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    required_paths = (
        "content/request.json",
        "content/page.html",
        "content/attachments.json",
    )
    root = snapshot_dir.resolve()
    observed_digests: dict[str, str] = {}
    for relative in required_paths:
        artifact = declared.get(relative)
        if not isinstance(artifact, dict):
            raise ValueError(f"required snapshot artifact missing: {relative}")
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"invalid snapshot artifact path: {relative}")
        digest = _digest(path)
        if digest != artifact.get("sha256") or path.stat().st_size != artifact.get("size"):
            raise ValueError(f"snapshot artifact drift: {relative}")
        observed_digests[relative] = digest

    request = _load_object(root / "content/request.json")
    request_id = str(request.get("id") or "")
    if request_id != str(request_entry.get("request_id") or ""):
        raise ValueError("snapshot request identifier mismatch")
    raw_state = request.get("described_state")
    if not isinstance(raw_state, str) or not raw_state:
        raise ValueError("request described_state is missing")
    mapping_bytes = mapping_path.read_bytes()
    mapping = yaml.safe_load(mapping_bytes)
    if not isinstance(mapping, dict) or not isinstance(mapping.get("source_states"), dict):
        raise ValueError("state mapping requires source_states")
    state_mapping = mapping["source_states"].get(raw_state)
    if not isinstance(state_mapping, dict):
        raise ValueError("request state is not mapped")
    normalised_state = state_mapping.get("normalised_state")
    if not isinstance(normalised_state, str) or not normalised_state:
        raise ValueError("normalised state is missing")

    counter = _CorrespondenceCounter()
    counter.feed((root / "content/page.html").read_text(encoding="utf-8"))
    if counter.total == 0:
        raise ValueError("snapshot has no correspondence evidence")
    attachments = json.loads((root / "content/attachments.json").read_bytes())
    if not isinstance(attachments, list):
        raise ValueError("attachment inventory must be a list")
    blockers: list[BoundedAuditBlocker] = ["human_mapping_review_pending"]
    if not attachments:
        blockers.append("no_nonempty_attachment_evidence")
    blockers.append("single_request_only")

    return BoundedRawStateAudit(
        request_id=request_id,
        snapshot_manifest_sha256=manifest_sha256,
        request_json_sha256=observed_digests["content/request.json"],
        page_html_sha256=observed_digests["content/page.html"],
        attachment_inventory_sha256=observed_digests["content/attachments.json"],
        mapping_sha256=sha256(mapping_bytes).hexdigest(),
        rights_reviewer=str(rights.get("reviewer") or ""),
        rights_reviewed_at=str(rights.get("reviewed_at") or ""),
        rights_purpose="foi-o-candidate-extraction",
        raw_state_value=raw_state,
        normalised_state=normalised_state,
        correspondence_count=counter.total,
        outgoing_correspondence_count=counter.outgoing,
        incoming_correspondence_count=counter.incoming,
        attachment_count=len(attachments),
        nonempty_attachment_evidence=bool(attachments),
        blockers=tuple(blockers),
    )
