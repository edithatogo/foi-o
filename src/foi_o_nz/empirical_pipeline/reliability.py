"""Pure descriptive reliability computation for locked empirical annotations."""

from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter
from typing import Any

from .annotations import AnnotationContractError, validate_locked_annotation_output
from .contracts import canonical_bytes, content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext

SHA256 = re.compile(r"^[0-9a-f]{64}$")
LOCKED_OUTPUT_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "run_id",
        "run_spec_sha256",
        "membership_sha256",
        "codebook_sha256",
        "calibration_sha256",
        "authorization_sha256",
        "packet_sha256",
        "source_bundle_sha256",
        "role_id",
        "annotations",
        "annotation_set_sha256",
    }
)
COMMON_LINEAGE_FIELDS = (
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "calibration_sha256",
    "authorization_sha256",
    "source_bundle_sha256",
)


class ReliabilityContractError(ValueError):
    """Raised when reliability evidence or configuration fails closed."""


def _require_capability(context: VerifiedExecutionContext) -> None:
    if not isinstance(context, VerifiedExecutionContext):
        raise ReliabilityContractError("verified execution context is required")
    try:
        context.require_capability("reliability", "reliability.compute_descriptive")
    except ExecutionContextError as error:
        raise ReliabilityContractError(str(error)) from error


def _locked_rows(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if set(output) != LOCKED_OUTPUT_FIELDS:
        raise ReliabilityContractError(
            "locked annotation lineage is incomplete or has extra fields"
        )
    if output.get("annotation_set_sha256") != content_sha256(output, "annotation_set_sha256"):
        raise ReliabilityContractError("invalid locked annotation set self-pin")
    if output.get("status") != "locked":
        raise ReliabilityContractError("annotation set is not locked")
    for field in (
        "run_spec_sha256",
        "membership_sha256",
        "codebook_sha256",
        "calibration_sha256",
        "authorization_sha256",
        "packet_sha256",
        "source_bundle_sha256",
    ):
        if SHA256.fullmatch(str(output.get(field))) is None:
            raise ReliabilityContractError(f"locked annotation {field} lineage is invalid")
    if not isinstance(output.get("run_id"), str) or not output["run_id"]:
        raise ReliabilityContractError("locked annotation run lineage is invalid")
    if not isinstance(output.get("role_id"), str) or not output["role_id"]:
        raise ReliabilityContractError("locked annotation role lineage is invalid")
    rows = output.get("annotations")
    if not isinstance(rows, list) or not rows:
        raise ReliabilityContractError("locked annotation set must contain records")
    parsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("annotation_sha256") != content_sha256(
            row, "annotation_sha256"
        ):
            raise ReliabilityContractError("invalid annotation record self-pin")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in parsed:
            raise ReliabilityContractError("annotation unit identities must be unique")
        if row.get("role_id") != output.get("role_id"):
            raise ReliabilityContractError("annotation role differs from its locked set")
        label, reason, spans = row.get("label"), row.get("abstention_reason"), row.get("spans")
        if label is None and (not isinstance(reason, str) or not reason):
            raise ReliabilityContractError("abstention requires a reason")
        if label is not None and (not isinstance(label, str) or not label or reason is not None):
            raise ReliabilityContractError("labeled annotation is malformed")
        if not isinstance(spans, list):
            raise ReliabilityContractError("annotation spans must be an array")
        parsed[unit_id] = row
    return parsed


def _membership_rows(membership: dict[str, Any]) -> dict[str, str]:
    if membership.get("membership_sha256") != content_sha256(membership, "membership_sha256"):
        raise ReliabilityContractError("invalid membership self-pin")
    if membership.get("status") != "candidate_membership":
        raise ReliabilityContractError("membership is not a candidate membership")
    rows = membership.get("membership")
    if not isinstance(rows, list) or not rows:
        raise ReliabilityContractError("membership must contain units")
    parsed: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ReliabilityContractError("membership row must be an object")
        unit_id, digest = row.get("unit_id"), row.get("unit_sha256")
        if not isinstance(unit_id, str) or not unit_id or unit_id in parsed:
            raise ReliabilityContractError("membership unit identities must be unique")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ReliabilityContractError("membership unit digest must be lowercase SHA-256")
        parsed[unit_id] = digest
    return parsed


def _kappa(
    labels_a: list[str | None], labels_b: list[str | None]
) -> tuple[float | None, str | None]:
    if not labels_a:
        return None, "no_eligible_pairs"
    count = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b, strict=True)) / count
    left, right = Counter(labels_a), Counter(labels_b)
    expected = sum(
        (left[label] / count) * (right[label] / count) for label in set(left) | set(right)
    )
    if math.isclose(expected, 1.0, abs_tol=1e-15):
        return None, "expected_agreement_equals_one"
    return (observed - expected) / (1 - expected), None


def _rate(numerator: int, denominator: int) -> dict[str, float | int]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "estimate": numerator / denominator,
    }


def _nullable_rate(numerator: int, denominator: int) -> dict[str, float | int | None]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "estimate": numerator / denominator if denominator else None,
    }


def _percentile(values: list[float], confidence: float) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    tail = (1 - confidence) / 2
    lower = max(0, min(len(ordered) - 1, math.floor(tail * len(ordered))))
    upper = max(0, min(len(ordered) - 1, math.ceil((1 - tail) * len(ordered)) - 1))
    return {"lower": ordered[lower], "upper": ordered[upper]}


def _bootstrap_indices(
    unit_ids: list[str],
    cluster_by_unit: dict[str, str] | None,
    rng: random.Random,
) -> list[int]:
    if cluster_by_unit is None:
        return [rng.randrange(len(unit_ids)) for _ in unit_ids]
    clusters: dict[str, list[int]] = {}
    for index, unit_id in enumerate(unit_ids):
        clusters.setdefault(cluster_by_unit[unit_id], []).append(index)
    cluster_ids = sorted(clusters)
    sampled = [cluster_ids[rng.randrange(len(cluster_ids))] for _ in cluster_ids]
    return [index for cluster_id in sampled for index in clusters[cluster_id]]


def compute_descriptive_reliability(
    *,
    context: VerifiedExecutionContext,
    left: dict[str, Any],
    right: dict[str, Any],
    left_packet: dict[str, Any],
    right_packet: dict[str, Any],
    seed: int,
    replicates: int,
    cluster_by_unit: dict[str, str] | None = None,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Compute descriptive agreement without making threshold or maturity decisions."""
    _require_capability(context)
    run_spec = context.run_spec
    membership = context.membership
    try:
        validate_locked_annotation_output(left, context=context, packet=left_packet)
        validate_locked_annotation_output(right, context=context, packet=right_packet)
    except AnnotationContractError as error:
        raise ReliabilityContractError(str(error)) from error
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ReliabilityContractError("bootstrap seed must be an integer")
    if not isinstance(replicates, int) or isinstance(replicates, bool) or replicates <= 0:
        raise ReliabilityContractError("bootstrap replicates must be a positive integer")
    if not isinstance(confidence, float) or not 0 < confidence < 1:
        raise ReliabilityContractError("bootstrap confidence must be between zero and one")
    membership_rows = _membership_rows(membership)
    left_rows, right_rows = _locked_rows(left), _locked_rows(right)
    if left.get("role_id") == right.get("role_id"):
        raise ReliabilityContractError("annotator roles must be distinct")
    for field in COMMON_LINEAGE_FIELDS:
        if left.get(field) != right.get(field):
            raise ReliabilityContractError(f"annotation {field} lineage mismatch")
    if left.get("packet_sha256") == right.get("packet_sha256"):
        raise ReliabilityContractError("distinct roles must have distinct packet lineage")
    if left.get("run_id") != run_spec.run_id:
        raise ReliabilityContractError("annotation run identity mismatch")
    if left.get("run_spec_sha256") != run_spec.run_spec_sha256:
        raise ReliabilityContractError("annotation run specification mismatch")
    if left.get("membership_sha256") != membership.get("membership_sha256"):
        raise ReliabilityContractError("annotation membership lineage mismatch")
    if set(left_rows) != set(right_rows):
        raise ReliabilityContractError("annotation unit sets differ")
    if set(left_rows) != set(membership_rows):
        raise ReliabilityContractError("annotation units differ from exact membership")
    for unit_id in left_rows:
        left_digest = left_rows[unit_id].get("unit_sha256")
        right_digest = right_rows[unit_id].get("unit_sha256")
        if left_digest != right_digest:
            raise ReliabilityContractError("cross-role unit identity digest mismatch")
        if left_digest != membership_rows[unit_id]:
            raise ReliabilityContractError("annotation unit digest differs from membership")
    unit_ids = sorted(left_rows)
    if cluster_by_unit is not None:
        if (
            not isinstance(cluster_by_unit, dict)
            or set(cluster_by_unit) != set(unit_ids)
            or any(not isinstance(value, str) or not value for value in cluster_by_unit.values())
        ):
            raise ReliabilityContractError("cluster mapping must be an exact nonempty partition")

    labels_a = [left_rows[unit_id]["label"] for unit_id in unit_ids]
    labels_b = [right_rows[unit_id]["label"] for unit_id in unit_ids]
    raw_count = sum(a == b for a, b in zip(labels_a, labels_b, strict=True))
    all_unit_span_count = sum(
        left_rows[unit_id]["spans"] == right_rows[unit_id]["spans"] for unit_id in unit_ids
    )
    span_eligible = [
        index
        for index, (left_label, right_label) in enumerate(zip(labels_a, labels_b, strict=True))
        if left_label is not None and left_label == right_label
    ]
    span_count = sum(
        left_rows[unit_ids[index]]["spans"] == right_rows[unit_ids[index]]["spans"]
        for index in span_eligible
    )
    abstention_count = sum(
        (left_rows[unit_id]["label"] is None) == (right_rows[unit_id]["label"] is None)
        for unit_id in unit_ids
    )
    kappa, undefined_reason = _kappa(labels_a, labels_b)

    rng = random.Random(seed)  # noqa: S311 - registered deterministic bootstrap
    raw_bootstrap: list[float] = []
    kappa_bootstrap: list[float] = []
    all_unit_span_bootstrap: list[float] = []
    span_bootstrap: list[float] = []
    abstention_bootstrap: list[float] = []
    for _ in range(replicates):
        indices = _bootstrap_indices(unit_ids, cluster_by_unit, rng)
        sample_a = [labels_a[index] for index in indices]
        sample_b = [labels_b[index] for index in indices]
        raw_bootstrap.append(
            sum(a == b for a, b in zip(sample_a, sample_b, strict=True)) / len(indices)
        )
        sampled_kappa, _ = _kappa(sample_a, sample_b)
        if sampled_kappa is not None:
            kappa_bootstrap.append(sampled_kappa)
        all_unit_span_bootstrap.append(
            sum(
                left_rows[unit_ids[index]]["spans"] == right_rows[unit_ids[index]]["spans"]
                for index in indices
            )
            / len(indices)
        )
        sampled_span_indices = [
            index
            for index in indices
            if labels_a[index] is not None and labels_a[index] == labels_b[index]
        ]
        if sampled_span_indices:
            span_bootstrap.append(
                sum(
                    left_rows[unit_ids[index]]["spans"] == right_rows[unit_ids[index]]["spans"]
                    for index in sampled_span_indices
                )
                / len(sampled_span_indices)
            )
        abstention_bootstrap.append(
            sum(
                (left_rows[unit_ids[index]]["label"] is None)
                == (right_rows[unit_ids[index]]["label"] is None)
                for index in indices
            )
            / len(indices)
        )

    record = {
        "schema_version": "foio.empirical-reliability.v1.0.0",
        "status": "computed_descriptive",
        "run_id": run_spec.run_id,
        "run_spec_sha256": run_spec.run_spec_sha256,
        "membership_sha256": membership["membership_sha256"],
        "codebook_sha256": left["codebook_sha256"],
        "population_sha256": context.population_sha256("reliability"),
        "calibration_artifact_sha256": context.calibration_artifact_sha256,
        "authorization_artifact_sha256": context.authorization_artifact_sha256,
        "calibration_sha256": left["calibration_sha256"],
        "authorization_sha256": left["authorization_sha256"],
        "source_bundle_sha256": left["source_bundle_sha256"],
        "annotation_lineage": [
            {
                "role_id": output["role_id"],
                "packet_sha256": output["packet_sha256"],
                "annotation_set_sha256": output["annotation_set_sha256"],
            }
            for output in sorted((left, right), key=lambda item: item["role_id"])
        ],
        "annotation_set_sha256": [
            left["annotation_set_sha256"],
            right["annotation_set_sha256"],
        ],
        "agreement_rows": [
            {
                "unit_id": unit_id,
                "unit_sha256": membership_rows[unit_id],
                "bootstrap_cluster_id": (
                    cluster_by_unit[unit_id] if cluster_by_unit is not None else unit_id
                ),
                "left_label": left_rows[unit_id]["label"],
                "right_label": right_rows[unit_id]["label"],
                "left_spans_sha256": hashlib.sha256(
                    canonical_bytes(left_rows[unit_id]["spans"])
                ).hexdigest(),
                "right_spans_sha256": hashlib.sha256(
                    canonical_bytes(right_rows[unit_id]["spans"])
                ).hexdigest(),
            }
            for unit_id in unit_ids
        ],
        "unit_count": len(unit_ids),
        "bootstrap": {
            "seed": seed,
            "replicates": replicates,
            "confidence": confidence,
            "unit": "duplicate_cluster" if cluster_by_unit is not None else "singleton",
            "cluster_count": (
                len(set(cluster_by_unit.values())) if cluster_by_unit is not None else len(unit_ids)
            ),
        },
        "raw_label_agreement": {
            **_rate(raw_count, len(unit_ids)),
            "ci": _percentile(raw_bootstrap, confidence),
        },
        "cohen_kappa": {
            "estimate": kappa,
            "ci": _percentile(kappa_bootstrap, confidence),
            "undefined_reason": undefined_reason,
            "bootstrap_replicates_valid": len(kappa_bootstrap),
            "bootstrap_replicates_undefined": replicates - len(kappa_bootstrap),
        },
        "all_unit_exact_span_agreement": {
            **_rate(all_unit_span_count, len(unit_ids)),
            "ci": _percentile(all_unit_span_bootstrap, confidence),
            "eligibility": "all_units_including_abstentions",
            "threshold_eligible": False,
        },
        "exact_span_agreement": {
            **_nullable_rate(span_count, len(span_eligible)),
            "ci": _percentile(span_bootstrap, confidence),
            "eligibility": "matching_non_null_label",
            "threshold_eligible": True,
            "bootstrap_replicates_valid": len(span_bootstrap),
            "bootstrap_replicates_undefined": replicates - len(span_bootstrap),
        },
        "abstention_agreement": {
            **_rate(abstention_count, len(unit_ids)),
            "ci": _percentile(abstention_bootstrap, confidence),
        },
        "threshold_satisfaction_authorized": False,
        "gold_promotion_authorized": False,
        "profile_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    return seal_record(record, "reliability_sha256")
