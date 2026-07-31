"""Canonical empirical frames with conserved populations and duplicate clusters."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, cast

from .contracts import canonical_bytes, content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext

SHA256 = re.compile(r"^[0-9a-f]{64}$")
UNIT_FIELDS = {"unit_id", "unit_sha256", "duplicate_key", "stratum"}
RIGHTS_DISPOSITION = "not_inferred"
FRAME_FIELDS = {
    "schema_version",
    "frame_id",
    "status",
    "source_population_sha256",
    "population",
    "excluded_ids",
    "unresolved_ids",
    "duplicate_registry",
    "units",
    "rights_disposition",
    "frame_sha256",
}
FRAME_APPROVAL_FIELDS = {
    "schema_version",
    "artifact_id",
    "candidate_frame_sha256",
    "source_population_sha256",
    "approver_identity",
    "artifact_sha256",
}


class FrameContractError(ValueError):
    """Raised when a frame or duplicate-cluster contract fails closed."""


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise FrameContractError(f"{label} must be a lowercase SHA-256")
    return value


def _require_nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrameContractError(f"{label} must be a nonempty string")
    return value


def validate_units(units: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Parse untrusted unit records and return their canonical ordering."""
    if not isinstance(units, list) or not units:
        raise FrameContractError("canonical units must be a nonempty list")
    parsed: list[dict[str, str]] = []
    ids: set[str] = set()
    digests: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict) or set(unit) != UNIT_FIELDS:
            raise FrameContractError("unit does not contain exactly the canonical fields")
        unit_id = _require_nonempty(unit["unit_id"], "unit identity")
        digest = _require_sha256(unit["unit_sha256"], "unit SHA-256")
        duplicate_key = _require_nonempty(unit["duplicate_key"], "duplicate key")
        stratum = _require_nonempty(unit["stratum"], "stratum")
        if unit_id in ids:
            raise FrameContractError("duplicate unit identity")
        if digest in digests:
            raise FrameContractError("duplicate unit SHA-256")
        ids.add(unit_id)
        digests.add(digest)
        parsed.append(
            {
                "unit_id": unit_id,
                "unit_sha256": digest,
                "duplicate_key": duplicate_key,
                "stratum": stratum,
            }
        )
    return sorted(parsed, key=lambda unit: (unit["unit_id"], unit["unit_sha256"]))


def _cluster_id(duplicate_key: str) -> str:
    digest = hashlib.sha256(canonical_bytes({"duplicate_key": duplicate_key})).hexdigest()
    return f"cluster:sha256:{digest}"


def build_duplicate_cluster_registry(units: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a deterministic, content-addressed duplicate-cluster registry."""
    canonical = validate_units(units)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for unit in canonical:
        groups[unit["duplicate_key"]].append(unit)
    clusters = []
    for duplicate_key, members in sorted(groups.items(), key=lambda item: _cluster_id(item[0])):
        clusters.append(
            {
                "cluster_id": _cluster_id(duplicate_key),
                "duplicate_key": duplicate_key,
                "unit_ids": [member["unit_id"] for member in members],
                "unit_sha256": [member["unit_sha256"] for member in members],
            }
        )
    return seal_record(
        {
            "schema_version": "foio.empirical-duplicate-cluster-registry.v1.0.0",
            "unit_count": len(canonical),
            "cluster_count": len(clusters),
            "clusters": clusters,
        },
        "registry_sha256",
    )


def validate_duplicate_cluster_registry(
    units: list[dict[str, Any]], registry: dict[str, Any]
) -> None:
    """Recompute the entire registry and reject omissions, mutation, or reordering."""
    if not isinstance(registry, dict):
        raise FrameContractError("duplicate registry must be an object")
    if registry.get("registry_sha256") != content_sha256(registry, "registry_sha256"):
        raise FrameContractError("invalid duplicate registry self-pin")
    if registry != build_duplicate_cluster_registry(units):
        raise FrameContractError("duplicate registry differs from canonical recomputation")


def _frame_units(units: list[dict[str, str]], registry: dict[str, Any]) -> list[dict[str, str]]:
    cluster_by_unit = {
        unit_id: cluster["cluster_id"]
        for cluster in registry["clusters"]
        for unit_id in cluster["unit_ids"]
    }
    return [{**unit, "duplicate_cluster_id": cluster_by_unit[unit["unit_id"]]} for unit in units]


def _canonical_ids(values: list[str], label: str) -> list[str]:
    if not isinstance(values, list):
        raise FrameContractError(f"{label} identities must be a list")
    parsed = [_require_nonempty(value, f"{label} identity") for value in values]
    if len(set(parsed)) != len(parsed):
        raise FrameContractError(f"{label} identities must be unique")
    return sorted(parsed)


def build_candidate_frame(
    *,
    frame_id: str,
    source_population_sha256: str,
    units: list[dict[str, Any]],
    predecessor_count: int,
    excluded_ids: list[str],
    unresolved_ids: list[str],
    duplicate_registry: dict[str, Any],
) -> dict[str, Any]:
    """Create a candidate frame without inferring source rights or authority."""
    canonical = validate_units(units)
    validate_duplicate_cluster_registry(canonical, duplicate_registry)
    record = {
        "schema_version": "foio.empirical-frame.v1.0.0",
        "frame_id": _require_nonempty(frame_id, "frame identity"),
        "status": "candidate",
        "source_population_sha256": _require_sha256(
            source_population_sha256, "source population SHA-256"
        ),
        "population": {
            "predecessor": predecessor_count,
            "included": len(canonical),
            "excluded": len(excluded_ids),
            "unresolved": len(unresolved_ids),
        },
        "excluded_ids": _canonical_ids(excluded_ids, "excluded"),
        "unresolved_ids": _canonical_ids(unresolved_ids, "unresolved"),
        "duplicate_registry": duplicate_registry,
        "units": _frame_units(canonical, duplicate_registry),
        "rights_disposition": RIGHTS_DISPOSITION,
    }
    sealed = seal_record(record, "frame_sha256")
    validate_frame(sealed)
    return sealed


def _candidate_projection(frame: dict[str, Any]) -> dict[str, Any]:
    projected = dict(frame)
    projected["status"] = "candidate"
    projected.pop("candidate_frame_sha256", None)
    projected.pop("transition_authorization_sha256", None)
    projected.pop("frame_sha256", None)
    return seal_record(projected, "frame_sha256")


def build_frame_approval(
    candidate: dict[str, Any], *, artifact_id: str, approver_identity: str
) -> dict[str, Any]:
    """Create an exact, content-addressed approval for one candidate frame."""
    validate_frame(candidate)
    if candidate["status"] != "candidate":
        raise FrameContractError("frame approval requires a candidate frame")
    return seal_record(
        {
            "schema_version": "foio.empirical-frame-approval.v1.0.0",
            "artifact_id": _require_nonempty(artifact_id, "frame approval identity"),
            "candidate_frame_sha256": candidate["frame_sha256"],
            "source_population_sha256": candidate["source_population_sha256"],
            "approver_identity": _require_nonempty(approver_identity, "frame approver identity"),
        },
        "artifact_sha256",
    )


def _validate_frame_approval(candidate: dict[str, Any], approval: object) -> str:
    if not isinstance(approval, dict) or set(approval) != FRAME_APPROVAL_FIELDS:
        raise FrameContractError("exact frame approval artifact is required")
    approval_record = cast("dict[str, Any]", approval)
    if approval_record.get("schema_version") != "foio.empirical-frame-approval.v1.0.0":
        raise FrameContractError("unsupported frame approval schema version")
    artifact_id = _require_nonempty(approval_record.get("artifact_id"), "frame approval identity")
    if not artifact_id.startswith("frame-approval:"):
        raise FrameContractError("frame approval identity is not registered for frame transition")
    _require_nonempty(approval_record.get("approver_identity"), "frame approver identity")
    digest = _require_sha256(approval_record.get("artifact_sha256"), "frame approval SHA-256")
    if digest != content_sha256(approval_record, "artifact_sha256"):
        raise FrameContractError("invalid frame approval self-pin")
    expected = {
        "candidate_frame_sha256": candidate["frame_sha256"],
        "source_population_sha256": candidate["source_population_sha256"],
    }
    if any(approval_record.get(field) != value for field, value in expected.items()):
        raise FrameContractError("frame approval differs from the exact candidate or population")
    return digest


def validate_frame(frame: dict[str, Any]) -> None:
    """Validate frame identity, conservation, cluster coverage, and transition pins."""
    if not isinstance(frame, dict) or frame.get("frame_sha256") != content_sha256(
        frame, "frame_sha256"
    ):
        raise FrameContractError("invalid frame self-pin")
    rights_fields = {key for key in frame if key.startswith("rights_")}
    if rights_fields != {"rights_disposition"} or frame["rights_disposition"] != RIGHTS_DISPOSITION:
        raise FrameContractError("frame must not infer rights eligibility")
    status = frame.get("status")
    if status not in {"candidate", "immutable"}:
        raise FrameContractError("unsupported frame status")
    expected_fields = FRAME_FIELDS | (
        {"candidate_frame_sha256", "transition_authorization_sha256"}
        if status == "immutable"
        else set()
    )
    if set(frame) != expected_fields:
        raise FrameContractError("frame contains fields outside its status contract")
    if frame["schema_version"] != "foio.empirical-frame.v1.0.0":
        raise FrameContractError("unsupported frame schema version")
    _require_nonempty(frame.get("frame_id"), "frame identity")
    _require_sha256(frame.get("source_population_sha256"), "source population SHA-256")
    raw_units = frame.get("units")
    if not isinstance(raw_units, list):
        raise FrameContractError("frame units must be a list")
    canonical_input: list[dict[str, Any]] = []
    for unit in raw_units:
        if not isinstance(unit, dict) or not set(unit) >= UNIT_FIELDS:
            raise FrameContractError("frame contains a malformed unit")
        canonical_input.append({key: unit[key] for key in UNIT_FIELDS})
    units = validate_units(canonical_input)
    if len(units) != len(raw_units):
        raise FrameContractError("frame contains a malformed unit")
    registry = frame.get("duplicate_registry")
    if not isinstance(registry, dict):
        raise FrameContractError("duplicate registry must be an object")
    validate_duplicate_cluster_registry(units, registry)
    if raw_units != _frame_units(units, registry):
        raise FrameContractError("frame duplicate-cluster assignments differ")

    excluded = _canonical_ids(frame["excluded_ids"], "excluded")
    unresolved = _canonical_ids(frame["unresolved_ids"], "unresolved")
    if excluded != frame["excluded_ids"] or unresolved != frame["unresolved_ids"]:
        raise FrameContractError("population identities are not canonically ordered")
    included_ids = {unit["unit_id"] for unit in units}
    excluded_ids = set(excluded)
    unresolved_ids = set(unresolved)
    if (
        len(excluded_ids) != len(excluded)
        or len(unresolved_ids) != len(unresolved)
        or included_ids & excluded_ids
        or included_ids & unresolved_ids
        or excluded_ids & unresolved_ids
    ):
        raise FrameContractError("population identities must be unique and disjoint")
    population = frame.get("population")
    if (
        not isinstance(population, dict)
        or set(population) != {"predecessor", "included", "excluded", "unresolved"}
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in population.values()
        )
    ):
        raise FrameContractError("frame population counts must be nonnegative integers")
    expected = {
        "predecessor": len(units) + len(excluded) + len(unresolved),
        "included": len(units),
        "excluded": len(excluded),
        "unresolved": len(unresolved),
    }
    if population != expected:
        raise FrameContractError("frame population is not exactly conserved")
    if status == "candidate":
        if "candidate_frame_sha256" in frame or "transition_authorization_sha256" in frame:
            raise FrameContractError("candidate contains immutable transition fields")
    else:
        _require_sha256(
            frame.get("transition_authorization_sha256"), "transition authorization SHA-256"
        )
        projected = _candidate_projection(frame)
        if frame.get("candidate_frame_sha256") != projected["frame_sha256"]:
            raise FrameContractError("candidate frame SHA-256 mismatch")


def finalize_frame(
    candidate: dict[str, Any],
    *,
    transition_authorization: dict[str, Any] | None = None,
    context: VerifiedExecutionContext | None = None,
) -> dict[str, Any]:
    """Freeze a candidate under a verified capability and registered approval."""
    if not isinstance(context, VerifiedExecutionContext):
        raise FrameContractError("verified execution context is required for frame finalization")
    validate_frame(candidate)
    if candidate["status"] != "candidate":
        raise FrameContractError("only a candidate frame can become immutable")
    authorization = _validate_frame_approval(candidate, transition_authorization)
    try:
        context.require_registered_approval(
            stage_kind="frame",
            capability="frame.finalize",
            artifact_prefix="frame-approval:",
            artifact_sha256=authorization,
        )
    except ExecutionContextError as error:
        raise FrameContractError(str(error)) from error
    immutable = dict(candidate)
    immutable["status"] = "immutable"
    immutable["candidate_frame_sha256"] = candidate["frame_sha256"]
    immutable["transition_authorization_sha256"] = authorization
    immutable = seal_record(immutable, "frame_sha256")
    validate_frame(immutable)
    return immutable
