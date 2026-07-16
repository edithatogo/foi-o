"""Independent verification and non-empirical comparison of governed runs."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.baseline_verification import verify_initial_baseline
from foi_o_nz.reextraction import GovernedReextractionPacket


class GovernedReextractionVerification(BaseModel):
    """Fail-closed proof for one local candidate re-extraction artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["foi-o.governed-reextraction-verification.v0.1.0"] = (
        "foi-o.governed-reextraction-verification.v0.1.0"
    )
    valid: Literal[True] = True
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    baseline_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    archive_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    pipeline_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    verifier_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    model_id: str = Field(min_length=1)
    model_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    model_weights_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_artifacts_verified: int = Field(ge=1)
    candidate_count: int = Field(ge=0)
    candidate_ids: tuple[str, ...]
    storage: Literal["local_only"] = "local_only"
    review_status: Literal["candidate"] = "candidate"
    human_promotion_required: Literal[True] = True
    model_applied: Literal[False] = False
    source_records_modified: Literal[False] = False
    empirical_comparison: Literal[False] = False
    publication_allowed: Literal[False] = False
    promotion_allowed: Literal[False] = False


class NonEmpiricalReextractionDelta(BaseModel):
    """Deterministic reproducibility delta without empirical claims."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["foi-o.non-empirical-reextraction-delta.v0.1.0"] = (
        "foi-o.non-empirical-reextraction-delta.v0.1.0"
    )
    classification: Literal["non_empirical_reproducibility_delta"] = (
        "non_empirical_reproducibility_delta"
    )
    baseline_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_identical: bool
    baseline_candidate_count: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    added_candidate_ids: tuple[str, ...]
    removed_candidate_ids: tuple[str, ...]
    changed_candidate_ids: tuple[str, ...]
    provenance_changed_candidate_ids: tuple[str, ...]
    candidate_sets_identical: bool
    empirical_comparison: Literal[False] = False
    empirical_claim_allowed: Literal[False] = False
    comparison_blockers: tuple[
        Literal["independent_annotation_pending", "synthetic_fixture_only"], ...
    ]
    review_status: Literal["candidate"] = "candidate"
    model_applied: Literal[False] = False
    source_records_modified: Literal[False] = False
    promotion_allowed: Literal[False] = False
    publication_allowed: Literal[False] = False


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verify_snapshot_artifacts(snapshot_dir: Path, source: dict[str, Any]) -> int:
    root = snapshot_dir.resolve()
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("source artifacts must be non-empty")
    for artifact in artifacts:
        _require(isinstance(artifact, dict), "source artifact must be an object")
        path = (root / str(artifact.get("path") or "")).resolve()
        _require(root in path.parents, "source artifact path escapes snapshot")
        _require(path.is_file(), "source artifact is missing")
        _require(_digest(path) == artifact.get("sha256"), "source artifact SHA-256 mismatch")
        _require(path.stat().st_size == artifact.get("size"), "source artifact size mismatch")
    return len(artifacts)


def verify_governed_reextraction(
    candidate_path: Path,
    *,
    baseline_path: Path,
    packet_path: Path,
    snapshot_dir: Path,
    contract_path: Path,
    expected_candidate_sha256: str,
    expected_packet_sha256: str,
) -> GovernedReextractionVerification:
    """Verify producer output independently against the immutable handoff."""
    _require(_digest(packet_path) == expected_packet_sha256, "packet SHA-256 mismatch")
    packet = GovernedReextractionPacket.model_validate(_load_object(packet_path))
    _require(_digest(candidate_path) == expected_candidate_sha256, "candidate SHA-256 mismatch")
    _require(_digest(baseline_path) == packet.baseline_sha256, "baseline SHA-256 mismatch")
    candidate = _load_object(candidate_path)
    source_path = snapshot_dir / "manifest.json"
    _require(_digest(source_path) == packet.source_manifest_sha256, "source manifest mismatch")
    source = _load_object(source_path)
    artifacts_verified = _verify_snapshot_artifacts(snapshot_dir, source)
    requests = source.get("requests")
    if not isinstance(requests, list) or len(requests) != 1:
        raise ValueError("expected one source request")
    _require(str(requests[0].get("request_id")) == packet.source_request_id, "request mismatch")
    _require(
        requests[0].get("content_sha256") == packet.source_content_sha256,
        "source content mismatch",
    )
    _require(candidate.get("review_status") == "candidate", "output must remain candidate")
    _require(candidate.get("human_promotion_required") is True, "promotion gate missing")
    _require(
        candidate.get("model", {}).get("applied_during_candidate_extraction") is False,
        "model execution claim is not permitted",
    )
    model = candidate.get("model", {})
    _require(model.get("model_id") == packet.model_id, "model identity mismatch")
    _require(model.get("revision") == packet.model_revision, "model revision mismatch")
    _require(
        model.get("weights_sha256") == packet.model_weights_sha256,
        "model weights mismatch",
    )
    records = candidate.get("manifest", {}).get("records")
    _require(isinstance(records, list), "candidate records must be a list")
    retrieved_at_values = {record.get("source_trace", {}).get("retrieved_at") for record in records}
    _require(len(retrieved_at_values) == 1, "candidate timestamps must be consistent")
    retrieved_at = next(iter(retrieved_at_values))
    _require(isinstance(retrieved_at, str) and retrieved_at, "candidate timestamp missing")
    independent = verify_initial_baseline(
        candidate_path,
        snapshot_dir=snapshot_dir,
        contract_path=contract_path,
        expected_baseline_sha256=expected_candidate_sha256,
        expected_source_manifest_sha256=packet.source_manifest_sha256,
        expected_contract_sha256=packet.contract_sha256,
        expected_pipeline_revision=packet.pipeline_revision,
        expected_archive_revision=packet.archive_revision,
        expected_retrieved_at=retrieved_at,
    )

    return GovernedReextractionVerification(
        packet_sha256=expected_packet_sha256,
        candidate_sha256=expected_candidate_sha256,
        baseline_sha256=packet.baseline_sha256,
        source_manifest_sha256=packet.source_manifest_sha256,
        source_content_sha256=packet.source_content_sha256,
        contract_sha256=packet.contract_sha256,
        archive_revision=packet.archive_revision,
        pipeline_revision=packet.pipeline_revision,
        verifier_revision=packet.verifier_revision,
        model_id=packet.model_id,
        model_revision=packet.model_revision,
        model_weights_sha256=packet.model_weights_sha256,
        source_artifacts_verified=artifacts_verified,
        candidate_count=independent["record_count"],
        candidate_ids=tuple(independent["candidate_ids"]),
    )


def _candidate_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = payload.get("manifest", {}).get("records")
    _require(isinstance(records, list), "candidate records must be a list")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        _require(isinstance(record, dict), "candidate record must be an object")
        record_id = record.get("record_id")
        _require(isinstance(record_id, str) and record_id, "candidate record_id missing")
        _require(record_id not in result, "duplicate candidate record_id")
        result[record_id] = record
    return result


def _without_retrieved_at(record: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(record)
    trace = normalized.get("source_trace")
    if isinstance(trace, dict):
        trace.pop("retrieved_at", None)
    return normalized


def compare_reextraction_to_baseline(
    candidate_path: Path,
    *,
    baseline_path: Path,
    packet_path: Path,
) -> NonEmpiricalReextractionDelta:
    """Compare candidate records deterministically without empirical claims."""
    candidate = _load_object(candidate_path)
    baseline = _load_object(baseline_path)
    packet = GovernedReextractionPacket.model_validate(_load_object(packet_path))
    _require(
        set(packet.comparison_blockers)
        == {"independent_annotation_pending", "synthetic_fixture_only"},
        "empirical comparison blockers must remain explicit",
    )
    for label, payload in (("candidate", candidate), ("baseline", baseline)):
        _require(
            payload.get("schema_version") == packet.baseline_schema_version,
            f"{label} schema mismatch",
        )
        _require(payload.get("review_status") == "candidate", f"{label} must remain candidate")
        _require(
            payload.get("human_promotion_required") is True,
            f"{label} promotion gate missing",
        )
        _require(
            payload.get("source_manifest_sha256") == packet.source_manifest_sha256,
            f"{label} source manifest mismatch",
        )
        _require(
            payload.get("contract", {}).get("manifest_sha256") == packet.contract_sha256,
            f"{label} contract mismatch",
        )
        _require(
            payload.get("archive_revision") == packet.archive_revision,
            f"{label} archive revision mismatch",
        )
        _require(
            payload.get("pipeline_revision") == packet.pipeline_revision,
            f"{label} pipeline revision mismatch",
        )
        model = payload.get("model", {})
        _require(model.get("model_id") == packet.model_id, f"{label} model identity mismatch")
        _require(
            model.get("revision") == packet.model_revision,
            f"{label} model revision mismatch",
        )
        _require(
            model.get("weights_sha256") == packet.model_weights_sha256,
            f"{label} model weights mismatch",
        )
        _require(
            model.get("applied_during_candidate_extraction") is False,
            f"{label} model execution prevents this bounded delta",
        )
    baseline_records = _candidate_map(baseline)
    candidate_records = _candidate_map(candidate)
    baseline_ids = set(baseline_records)
    candidate_ids = set(candidate_records)
    common_ids = baseline_ids & candidate_ids
    changed = sorted(
        record_id
        for record_id in common_ids
        if _without_retrieved_at(baseline_records[record_id])
        != _without_retrieved_at(candidate_records[record_id])
    )
    provenance_changed = sorted(
        record_id
        for record_id in common_ids
        if baseline_records[record_id].get("source_trace", {}).get("retrieved_at")
        != candidate_records[record_id].get("source_trace", {}).get("retrieved_at")
    )
    added = sorted(candidate_ids - baseline_ids)
    removed = sorted(baseline_ids - candidate_ids)
    return NonEmpiricalReextractionDelta(
        baseline_sha256=_digest(baseline_path),
        candidate_sha256=_digest(candidate_path),
        byte_identical=baseline_path.read_bytes() == candidate_path.read_bytes(),
        baseline_candidate_count=len(baseline_records),
        candidate_count=len(candidate_records),
        added_candidate_ids=tuple(added),
        removed_candidate_ids=tuple(removed),
        changed_candidate_ids=tuple(changed),
        provenance_changed_candidate_ids=tuple(provenance_changed),
        candidate_sets_identical=not (added or removed or changed),
        comparison_blockers=packet.comparison_blockers,
    )
