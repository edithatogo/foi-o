"""Deterministic, cluster-aware empirical membership selection."""

from __future__ import annotations

import hashlib
from typing import Any, cast

from .contracts import canonical_bytes, content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext
from .frames import FrameContractError, validate_frame

DESIGNS = {"simple_random_without_replacement", "census", "complement_holdout"}
SAMPLING_UNITS = {"unit", "duplicate_cluster"}
SAMPLING_APPROVAL_FIELDS = {
    "schema_version",
    "artifact_id",
    "frame_sha256",
    "source_population_sha256",
    "duplicate_registry_sha256",
    "design",
    "sampling_unit",
    "seed",
    "sample_size",
    "selection_algorithm",
    "cluster_rule",
    "prior_membership_sha256",
    "approver_identity",
    "artifact_sha256",
}
DENIED_CAPABILITIES = (
    "adjudication.execute",
    "annotation.execute",
    "extractor_metrics.compute",
    "gold.promote",
    "profile.promote",
    "publication.release",
    "redistribution.release",
    "training.execute",
)


class SamplingContractError(ValueError):
    """Raised when sampling or membership validation fails closed."""


def _require_immutable_frame(frame: dict[str, Any]) -> None:
    try:
        validate_frame(frame)
    except FrameContractError as error:
        raise SamplingContractError(f"invalid frame: {error}") from error
    if frame["status"] != "immutable":
        raise SamplingContractError("sampling requires an immutable frame")


def _entities(frame: dict[str, Any], sampling_unit: str) -> list[tuple[str, list[dict[str, Any]]]]:
    if sampling_unit == "unit":
        return [(unit["unit_id"], [unit]) for unit in frame["units"]]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for unit in frame["units"]:
        grouped.setdefault(unit["duplicate_cluster_id"], []).append(unit)
    return [
        (cluster_id, sorted(units, key=lambda unit: unit["unit_id"]))
        for cluster_id, units in sorted(grouped.items())
    ]


def _selected_entities(
    entities: list[tuple[str, list[dict[str, Any]]]],
    *,
    design: str,
    seed: int,
    sample_size: int,
    prior_ids: set[str],
) -> tuple[list[tuple[str, list[dict[str, Any]]]], float]:
    if design == "census":
        if sample_size != len(entities):
            raise SamplingContractError("census sample size must equal its population")
        return entities, 1.0
    if design == "complement_holdout":
        selected = [
            entity for entity in entities if not {unit["unit_id"] for unit in entity[1]} & prior_ids
        ]
        if sample_size != len(selected):
            raise SamplingContractError("complement sample size differs from exact remainder")
        return selected, 1.0
    if sample_size <= 0 or sample_size > len(entities):
        raise SamplingContractError("sample size is outside the sampling-unit population")
    ranked = sorted(
        entities,
        key=lambda entity: (
            hashlib.sha256(
                canonical_bytes({"seed": seed, "sampling_entity_id": entity[0]})
            ).hexdigest(),
            entity[0],
        ),
    )
    selected = sorted(ranked[:sample_size], key=lambda entity: entity[0])
    return selected, sample_size / len(entities)


def _cluster_rule(sampling_unit: str) -> str:
    return (
        "whole_duplicate_clusters.v1"
        if sampling_unit == "duplicate_cluster"
        else "independent_units.v1"
    )


def build_sampling_approval(
    frame: dict[str, Any],
    *,
    artifact_id: str,
    approver_identity: str,
    design: str,
    sampling_unit: str,
    seed: int,
    sample_size: int,
    prior_membership: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an exact approval for one immutable-frame sampling operation."""
    _require_immutable_frame(frame)
    if design not in DESIGNS:
        raise SamplingContractError("sampling approval contains an unsupported design")
    if sampling_unit not in SAMPLING_UNITS:
        raise SamplingContractError("sampling approval contains an unsupported sampling unit")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise SamplingContractError("sampling approval seed must be an integer")
    if not isinstance(sample_size, int) or isinstance(sample_size, bool):
        raise SamplingContractError("sampling approval sample size must be an integer")
    if not isinstance(artifact_id, str) or not artifact_id.startswith("sampling-approval:"):
        raise SamplingContractError("sampling approval identity is invalid")
    if not isinstance(approver_identity, str) or not approver_identity:
        raise SamplingContractError("sampling approver identity is invalid")
    prior_sha = None
    if prior_membership is not None:
        prior_sha = prior_membership.get("membership_sha256")
        if not isinstance(prior_sha, str) or len(prior_sha) != 64:
            raise SamplingContractError("prior membership SHA-256 is invalid")
    return seal_record(
        {
            "schema_version": "foio.empirical-sampling-approval.v1.0.0",
            "artifact_id": artifact_id,
            "frame_sha256": frame["frame_sha256"],
            "source_population_sha256": frame["source_population_sha256"],
            "duplicate_registry_sha256": frame["duplicate_registry"]["registry_sha256"],
            "design": design,
            "sampling_unit": sampling_unit,
            "seed": seed,
            "sample_size": sample_size,
            "selection_algorithm": "sha256-ranked-without-replacement.v1",
            "cluster_rule": _cluster_rule(sampling_unit),
            "prior_membership_sha256": prior_sha,
            "approver_identity": approver_identity,
        },
        "artifact_sha256",
    )


def _validate_sampling_approval(
    frame: dict[str, Any],
    approval: object,
    *,
    design: str,
    sampling_unit: str,
    seed: int,
    sample_size: int,
    prior_membership: dict[str, Any] | None,
) -> str:
    if not isinstance(approval, dict) or set(approval) != SAMPLING_APPROVAL_FIELDS:
        raise SamplingContractError("exact sampling approval artifact is required")
    approval_record = cast("dict[str, Any]", approval)
    if approval_record.get("schema_version") != "foio.empirical-sampling-approval.v1.0.0":
        raise SamplingContractError("unsupported sampling approval schema version")
    digest = approval_record.get("artifact_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise SamplingContractError("sampling approval SHA-256 is invalid")
    if digest != content_sha256(approval_record, "artifact_sha256"):
        raise SamplingContractError("invalid sampling approval self-pin")
    prior_sha = prior_membership.get("membership_sha256") if prior_membership is not None else None
    expected = {
        "frame_sha256": frame["frame_sha256"],
        "source_population_sha256": frame["source_population_sha256"],
        "duplicate_registry_sha256": frame["duplicate_registry"]["registry_sha256"],
        "design": design,
        "sampling_unit": sampling_unit,
        "seed": seed,
        "sample_size": sample_size,
        "selection_algorithm": "sha256-ranked-without-replacement.v1",
        "cluster_rule": _cluster_rule(sampling_unit),
        "prior_membership_sha256": prior_sha,
    }
    if any(approval_record.get(field) != value for field, value in expected.items()):
        raise SamplingContractError("sampling approval differs from exact frame or design")
    if not str(approval_record.get("artifact_id", "")).startswith("sampling-approval:"):
        raise SamplingContractError("sampling approval identity is invalid")
    if (
        not isinstance(approval_record.get("approver_identity"), str)
        or not approval_record["approver_identity"]
    ):
        raise SamplingContractError("sampling approver identity is invalid")
    return digest


def _validate_prior(
    frame: dict[str, Any],
    prior_membership: dict[str, Any] | None,
    sampling_unit: str,
) -> tuple[set[str], str | None]:
    if prior_membership is None:
        raise SamplingContractError("complement holdout requires a prior membership")
    if prior_membership.get("design") == "complement_holdout":
        raise SamplingContractError("nested complement memberships are unsupported")
    if prior_membership.get("membership_sha256") != content_sha256(
        prior_membership, "membership_sha256"
    ):
        raise SamplingContractError("invalid prior membership self-pin")
    prior_design = prior_membership.get("design")
    prior_sampling_unit = prior_membership.get("sampling_unit")
    prior_seed = prior_membership.get("seed")
    prior_size = prior_membership.get("selected_sampling_unit_count")
    prior_approval = prior_membership.get("sampling_approval_sha256")
    if (
        not isinstance(prior_design, str)
        or not isinstance(prior_sampling_unit, str)
        or not isinstance(prior_seed, int)
        or isinstance(prior_seed, bool)
        or not isinstance(prior_size, int)
        or isinstance(prior_size, bool)
        or not isinstance(prior_approval, str)
    ):
        raise SamplingContractError("prior membership design fields are invalid")
    expected = _build_membership_record(
        frame,
        design=prior_design,
        sampling_unit=prior_sampling_unit,
        seed=prior_seed,
        sample_size=prior_size,
        sampling_approval_sha256=prior_approval,
        prior_membership=None,
    )
    if prior_membership != expected:
        raise SamplingContractError("prior membership differs from exact recomputation")
    if prior_membership["sampling_unit"] != sampling_unit:
        raise SamplingContractError("prior membership uses a different sampling unit")
    prior_ids = {row["unit_id"] for row in prior_membership["membership"]}
    if sampling_unit == "duplicate_cluster":
        for _, units in _entities(frame, sampling_unit):
            cluster_ids = {unit["unit_id"] for unit in units}
            if cluster_ids & prior_ids and not cluster_ids <= prior_ids:
                raise SamplingContractError("prior membership contains a partial duplicate cluster")
    return prior_ids, prior_membership["membership_sha256"]


def _build_membership_record(
    frame: dict[str, Any],
    *,
    design: str,
    sampling_unit: str,
    seed: int,
    sample_size: int,
    sampling_approval_sha256: str,
    prior_membership: dict[str, Any] | None,
) -> dict[str, Any]:
    entities = _entities(frame, sampling_unit)
    prior_ids: set[str] = set()
    prior_sha256: str | None = None
    if design == "complement_holdout":
        prior_ids, prior_sha256 = _validate_prior(frame, prior_membership, sampling_unit)
    elif prior_membership is not None:
        raise SamplingContractError("prior membership is valid only for a complement holdout")
    selected, probability = _selected_entities(
        entities,
        design=design,
        seed=seed,
        sample_size=sample_size,
        prior_ids=prior_ids,
    )
    rows = [
        {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "duplicate_cluster_id": unit["duplicate_cluster_id"],
            "stratum": unit["stratum"],
            "inclusion_probability": probability,
            "sampling_weight": 1 / probability,
        }
        for _, units in selected
        for unit in units
    ]
    rows.sort(key=lambda row: (row["unit_id"], row["unit_sha256"]))
    record: dict[str, Any] = {
        "schema_version": "foio.empirical-sampling-membership.v1.0.0",
        "status": "candidate_membership",
        "frame_id": frame["frame_id"],
        "frame_sha256": frame["frame_sha256"],
        "sampling_approval_sha256": sampling_approval_sha256,
        "design": design,
        "sampling_unit": sampling_unit,
        "seed": seed,
        "selection_algorithm": "sha256-ranked-without-replacement.v1",
        "population_unit_count": len(frame["units"]),
        "population_sampling_unit_count": len(entities),
        "selected_unit_count": len(rows),
        "selected_sampling_unit_count": len(selected),
        "excluded_unit_count": len(frame["units"]) - len(rows),
        "probability_basis": (
            "conditional_on_pinned_prior_membership"
            if design == "complement_holdout"
            else "unconditional_design"
        ),
        "membership": rows,
        "allowed_capabilities": ["sampling.membership.prepare"],
        "denied_capabilities": list(DENIED_CAPABILITIES),
        "annotation_authorized": False,
        "adjudication_authorized": False,
        "extractor_metrics_authorized": False,
        "profile_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    if prior_sha256 is not None:
        record["prior_membership_sha256"] = prior_sha256
    return seal_record(record, "membership_sha256")


def build_membership(
    frame: dict[str, Any],
    *,
    context: VerifiedExecutionContext | None = None,
    sampling_approval: dict[str, Any] | None = None,
    design: str,
    sampling_unit: str,
    seed: int,
    sample_size: int,
    prior_membership: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build membership under a verified capability and registered approval."""
    if not isinstance(context, VerifiedExecutionContext):
        raise SamplingContractError("verified execution context is required for sampling")
    _require_immutable_frame(frame)
    if design not in DESIGNS:
        raise SamplingContractError("unsupported sampling design")
    if sampling_unit not in SAMPLING_UNITS:
        raise SamplingContractError("unsupported sampling unit")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise SamplingContractError("seed must be an integer")
    if not isinstance(sample_size, int) or isinstance(sample_size, bool):
        raise SamplingContractError("sample size must be an integer")
    approval_sha256 = _validate_sampling_approval(
        frame,
        sampling_approval,
        design=design,
        sampling_unit=sampling_unit,
        seed=seed,
        sample_size=sample_size,
        prior_membership=prior_membership,
    )
    try:
        context.require_registered_approval(
            stage_kind="sample",
            capability="sampling.membership.prepare",
            artifact_prefix="sampling-approval:",
            artifact_sha256=approval_sha256,
        )
    except ExecutionContextError as error:
        raise SamplingContractError(str(error)) from error
    return _build_membership_record(
        frame,
        design=design,
        sampling_unit=sampling_unit,
        seed=seed,
        sample_size=sample_size,
        sampling_approval_sha256=approval_sha256,
        prior_membership=prior_membership,
    )


def validate_membership(
    frame: dict[str, Any],
    membership: dict[str, Any],
    *,
    context: VerifiedExecutionContext | None = None,
    sampling_approval: dict[str, Any] | None = None,
    prior_membership: dict[str, Any] | None = None,
) -> None:
    """Recompute exact membership, probabilities, weights, boundaries, and self-pin."""
    _require_immutable_frame(frame)
    if not isinstance(membership, dict) or membership.get("membership_sha256") != content_sha256(
        membership, "membership_sha256"
    ):
        raise SamplingContractError("invalid membership self-pin")
    try:
        expected = build_membership(
            frame,
            context=context,
            sampling_approval=sampling_approval,
            design=membership["design"],
            sampling_unit=membership["sampling_unit"],
            seed=membership["seed"],
            sample_size=membership["selected_sampling_unit_count"],
            prior_membership=prior_membership,
        )
    except KeyError as error:
        raise SamplingContractError(f"membership is missing {error.args[0]}") from error
    if membership != expected:
        raise SamplingContractError("membership differs from exact deterministic recomputation")
