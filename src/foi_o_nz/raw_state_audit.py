"""Read-only readiness audit for FYI raw-state mapping evidence."""

from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

AuditBlocker = Literal[
    "missing_state_values",
    "unmapped_source_states",
    "no_correspondence_evidence",
    "no_attachment_evidence",
]


class RawStateAuditReadiness(BaseModel):
    """Aggregate whether a manifest can support correspondence-backed mapping review."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o.raw-state-audit-readiness.v0.1.0"] = (
        "foi-o.raw-state-audit-readiness.v0.1.0"
    )
    dataset_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_count: int = Field(ge=0)
    observed_state_counts: dict[str, int]
    records_missing_state: int = Field(ge=0)
    records_with_mapped_state: int = Field(ge=0)
    unmapped_nonempty_states: list[str]
    records_with_correspondence: int = Field(ge=0)
    records_with_nonempty_attachments: int = Field(ge=0)
    ready_for_mapping_audit: bool
    blockers: list[AuditBlocker]
    source_records_modified: Literal[False] = False


def _has_evidence(value: object) -> bool:
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return value is not None


def audit_raw_state_inputs(
    manifest_path: Path,
    *,
    mapping_path: Path,
    dataset_revision: str,
    expected_manifest_sha256: str,
) -> RawStateAuditReadiness:
    """Inspect aggregate state/evidence coverage without modifying source records."""
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha256 = sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != expected_manifest_sha256:
        raise ValueError(
            f"manifest SHA-256 mismatch: expected {expected_manifest_sha256}, "
            f"observed {manifest_sha256}"
        )
    payload = json.loads(manifest_bytes)
    if not isinstance(payload, dict) or not isinstance(payload.get("requests"), list):
        raise ValueError("archive manifest requires an object with a requests array")
    requests = payload["requests"]
    if not all(isinstance(record, dict) for record in requests):
        raise ValueError("every archive request must be a JSON object")

    mapping_bytes = mapping_path.read_bytes()
    mapping = yaml.safe_load(mapping_bytes)
    if not isinstance(mapping, dict) or not isinstance(mapping.get("source_states"), dict):
        raise ValueError("state mapping requires a source_states object")
    mapped_states = set(mapping["source_states"])

    states = [str(record.get("state") or "").strip() for record in requests]
    state_counts = dict(sorted(Counter(states).items()))
    nonempty_states = {state for state in states if state}
    missing_states = state_counts.get("", 0)
    unmapped_states = sorted(nonempty_states - mapped_states)
    mapped_records = sum(count for state, count in state_counts.items() if state in mapped_states)
    correspondence_records = sum(_has_evidence(record.get("correspondence")) for record in requests)
    attachment_records = sum(_has_evidence(record.get("attachments")) for record in requests)

    blockers: list[AuditBlocker] = []
    if missing_states:
        blockers.append("missing_state_values")
    if unmapped_states:
        blockers.append("unmapped_source_states")
    if correspondence_records == 0:
        blockers.append("no_correspondence_evidence")
    if attachment_records == 0:
        blockers.append("no_attachment_evidence")

    return RawStateAuditReadiness(
        dataset_revision=dataset_revision,
        manifest_sha256=manifest_sha256,
        mapping_sha256=sha256(mapping_bytes).hexdigest(),
        record_count=len(requests),
        observed_state_counts=state_counts,
        records_missing_state=missing_states,
        records_with_mapped_state=mapped_records,
        unmapped_nonempty_states=unmapped_states,
        records_with_correspondence=correspondence_records,
        records_with_nonempty_attachments=attachment_records,
        ready_for_mapping_audit=not blockers,
        blockers=blockers,
    )
