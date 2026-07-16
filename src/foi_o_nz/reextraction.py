"""Fail-closed input auditing for governed FOI-O re-extraction runs."""

from __future__ import annotations

import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.io import write_json

SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
AuditBlocker = Literal[
    "declared_record_count_mismatch",
    "duplicate_request_ids",
    "invalid_content_sha256",
    "missing_declared_license",
    "missing_request_id",
]


class ReextractionInputAudit(BaseModel):
    """Aggregate integrity and rights audit for one immutable archive manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o.reextraction-input-audit.v0.1.0"] = (
        "foi-o.reextraction-input-audit.v0.1.0"
    )
    dataset_repository: str = Field(min_length=1)
    dataset_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    configuration: str = Field(min_length=1)
    split: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_generated_at: str = Field(min_length=1)
    source_manifest_version: str = Field(min_length=1)
    declared_record_count: int = Field(ge=0)
    record_count: int = Field(ge=0)
    records_with_valid_content_sha256: int = Field(ge=0)
    records_with_invalid_content_sha256: int = Field(ge=0)
    records_with_declared_license: int = Field(ge=0)
    records_without_declared_license: int = Field(ge=0)
    records_missing_request_id: int = Field(ge=0)
    duplicate_request_ids: list[str]
    rights_status: Literal["complete", "incomplete"]
    ready_for_reextraction: bool
    blockers: list[AuditBlocker]
    source_records_modified: Literal[False] = False


def audit_reextraction_input(
    manifest_path: Path,
    *,
    dataset_repository: str,
    dataset_revision: str,
    configuration: str,
    split: str,
    expected_manifest_sha256: str,
) -> ReextractionInputAudit:
    """Audit one immutable archive manifest without modifying source records."""
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha256 = sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != expected_manifest_sha256:
        raise ValueError(
            f"manifest SHA-256 mismatch: expected {expected_manifest_sha256}, "
            f"observed {manifest_sha256}"
        )

    payload = json.loads(manifest_bytes)
    if not isinstance(payload, dict):
        raise ValueError("archive manifest must be a JSON object")
    meta = payload.get("meta")
    requests = payload.get("requests")
    if not isinstance(meta, dict) or not isinstance(requests, list):
        raise ValueError("archive manifest requires object meta and array requests")

    request_ids: list[str] = []
    missing_request_ids = 0
    valid_digests = 0
    declared_licenses = 0
    for record in requests:
        if not isinstance(record, dict):
            raise ValueError("every archive request must be a JSON object")
        request_id = record.get("request_id")
        if request_id is None or str(request_id).strip() == "":
            missing_request_ids += 1
        else:
            request_ids.append(str(request_id))
        content_digest = record.get("content_sha256")
        if isinstance(content_digest, str) and SHA256_PATTERN.fullmatch(content_digest):
            valid_digests += 1
        license_value = record.get("license")
        if isinstance(license_value, str) and license_value.strip():
            declared_licenses += 1

    request_id_counts = Counter(request_ids)
    duplicate_request_ids = sorted(
        request_id for request_id, count in request_id_counts.items() if count > 1
    )
    record_count = len(requests)
    declared_record_count = meta.get("record_count")
    if not isinstance(declared_record_count, int) or declared_record_count < 0:
        raise ValueError("manifest meta.record_count must be a non-negative integer")
    source_generated_at = meta.get("generated_at")
    source_manifest_version = meta.get("version")
    if not isinstance(source_generated_at, str) or not source_generated_at:
        raise ValueError("manifest meta.generated_at must be a non-empty string")
    if not isinstance(source_manifest_version, str) or not source_manifest_version:
        raise ValueError("manifest meta.version must be a non-empty string")

    blockers: list[AuditBlocker] = []
    if declared_record_count != record_count:
        blockers.append("declared_record_count_mismatch")
    if duplicate_request_ids:
        blockers.append("duplicate_request_ids")
    if valid_digests != record_count:
        blockers.append("invalid_content_sha256")
    if declared_licenses != record_count:
        blockers.append("missing_declared_license")
    if missing_request_ids:
        blockers.append("missing_request_id")

    return ReextractionInputAudit(
        dataset_repository=dataset_repository,
        dataset_revision=dataset_revision,
        configuration=configuration,
        split=split,
        manifest_sha256=manifest_sha256,
        source_generated_at=source_generated_at,
        source_manifest_version=source_manifest_version,
        declared_record_count=declared_record_count,
        record_count=record_count,
        records_with_valid_content_sha256=valid_digests,
        records_with_invalid_content_sha256=record_count - valid_digests,
        records_with_declared_license=declared_licenses,
        records_without_declared_license=record_count - declared_licenses,
        records_missing_request_id=missing_request_ids,
        duplicate_request_ids=duplicate_request_ids,
        rights_status="complete" if declared_licenses == record_count else "incomplete",
        ready_for_reextraction=not blockers,
        blockers=blockers,
    )


def write_reextraction_input_audit(
    manifest_path: Path,
    output: Path,
    *,
    dataset_repository: str,
    dataset_revision: str,
    configuration: str,
    split: str,
    expected_manifest_sha256: str,
) -> dict[str, object]:
    """Write a portable audit report while leaving the input manifest untouched."""
    report = audit_reextraction_input(
        manifest_path,
        dataset_repository=dataset_repository,
        dataset_revision=dataset_revision,
        configuration=configuration,
        split=split,
        expected_manifest_sha256=expected_manifest_sha256,
    )
    write_json(output, report.model_dump(mode="json"))
    return {
        "output": str(output),
        "ready_for_reextraction": report.ready_for_reextraction,
        "record_count": report.record_count,
        "blockers": report.blockers,
    }
