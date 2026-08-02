"""Pending-only maturity threshold packets with explicit evidence lifecycle."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from .contracts import RunSpecification, content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext
from .metric_validation import MetricArtifactError, threshold_metric, validate_metric_artifact

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "json"
    / "australian-maturity-decision-candidate.schema.json"
)


class MaturityContractError(ValueError):
    """Raised when maturity evidence or a candidate packet fails closed."""


LINEAGE_FIELDS = (
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "population_sha256",
    "authorization_artifact_sha256",
    "calibration_artifact_sha256",
)
SOURCE_METRIC_LINEAGE_FIELDS = (
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "population_sha256",
    "authorization_artifact_sha256",
    "calibration_artifact_sha256",
)


def validate_executable_lifecycle(run_spec: RunSpecification | dict[str, Any]) -> None:
    """Reject execution from retired or internally inconsistent empirical runs."""
    raw = run_spec.raw if isinstance(run_spec, RunSpecification) else run_spec
    assessment = raw.get("assessment_status")
    disposition = raw.get("lifecycle_disposition")
    allowed = {
        "active": {"active", "opaque_producer"},
        "candidate": {"active", "opaque_producer"},
        "superseded": {"superseded"},
        "invalidated": {"invalidated"},
    }
    if assessment not in allowed or disposition not in allowed[assessment]:
        raise MaturityContractError("assessment status and lifecycle disposition are incompatible")
    if assessment in {"superseded", "invalidated"} or disposition in {
        "superseded",
        "invalidated",
    }:
        raise MaturityContractError("retired empirical run cannot execute stages")


def _require_capability(context: VerifiedExecutionContext) -> None:
    if not isinstance(context, VerifiedExecutionContext):
        raise MaturityContractError("verified execution context is required")
    try:
        context.require_capability("maturity", "maturity.compare_thresholds")
    except ExecutionContextError as error:
        raise MaturityContractError(str(error)) from error


def _registered_artifact(run_spec: RunSpecification, prefix: str, digest: str) -> None:
    matches = [
        artifact
        for artifact in run_spec.raw.get("referenced_artifacts", [])
        if artifact.get("artifact_id", "").startswith(prefix) and artifact.get("sha256") == digest
    ]
    if len(matches) != 1:
        raise MaturityContractError(f"{prefix.rstrip(':')} artifact is not uniquely registered")


def _require_metric_pair_lineage(
    context: VerifiedExecutionContext,
    reliability: dict[str, Any],
    extractor_metrics: dict[str, Any],
) -> dict[str, str]:
    source = {field: reliability.get(field) for field in SOURCE_METRIC_LINEAGE_FIELDS}
    if any(
        not isinstance(value, str) or len(value) != 64
        for field, value in source.items()
        if field != "run_id"
    ) or not isinstance(source["run_id"], str):
        raise MaturityContractError("source metric lineage is invalid")
    if any(extractor_metrics.get(field) != value for field, value in source.items()):
        raise MaturityContractError("registered metric artifacts do not share exact lineage")
    expected_context = {
        "membership_sha256": context.membership_sha256,
        "codebook_sha256": context.codebook_sha256,
        "population_sha256": context.population_sha256("maturity"),
        "authorization_artifact_sha256": context.authorization_artifact_sha256,
        "calibration_artifact_sha256": context.calibration_artifact_sha256,
    }
    if any(source[field] != value for field, value in expected_context.items()):
        raise MaturityContractError("source metric lineage differs from maturity review context")
    return {field: cast("str", value) for field, value in source.items()}


def _artifact_pin(artifact: dict[str, Any], field: str) -> str:
    kind = "reliability" if field == "reliability_sha256" else "extractor_metrics"
    try:
        return validate_metric_artifact(artifact, kind)
    except MetricArtifactError as error:
        raise MaturityContractError(str(error)) from error


def _metric(root: dict[str, Any], kind: str, path: str) -> float:
    try:
        return threshold_metric(root, kind, path)
    except MetricArtifactError as error:
        raise MaturityContractError(str(error)) from error


def _compare(observed: float, operator: str, threshold: float) -> bool:
    return {
        ">=": observed >= threshold,
        ">": observed > threshold,
        "<=": observed <= threshold,
        "<": observed < threshold,
        "==": observed == threshold,
    }[operator]


def _validate_lifecycle(lifecycle: list[dict[str, Any]], current: set[str]) -> list[dict[str, Any]]:
    if not isinstance(lifecycle, list):
        raise MaturityContractError("evidence lifecycle must be an array")
    by_digest: dict[str, dict[str, Any]] = {}
    for row in lifecycle:
        if not isinstance(row, dict) or set(row) != {
            "artifact_sha256",
            "disposition",
            "superseded_by_sha256",
            "reason",
        }:
            raise MaturityContractError("evidence lifecycle row violates strict contract")
        digest = row["artifact_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or digest in by_digest:
            raise MaturityContractError(
                "evidence lifecycle identities must be unique SHA-256 values"
            )
        disposition = row["disposition"]
        target, reason = row["superseded_by_sha256"], row["reason"]
        if disposition == "active" and (target is not None or reason is not None):
            raise MaturityContractError("active evidence cannot carry retirement metadata")
        if disposition == "superseded" and (
            not isinstance(target, str)
            or len(target) != 64
            or not isinstance(reason, str)
            or not reason
        ):
            raise MaturityContractError("superseded evidence requires target and reason")
        if disposition == "invalidated" and (
            target is not None or not isinstance(reason, str) or not reason
        ):
            raise MaturityContractError("invalidated evidence requires a reason and no successor")
        if disposition not in {"active", "superseded", "invalidated"}:
            raise MaturityContractError("unsupported evidence lifecycle disposition")
        by_digest[digest] = row
    if not current <= set(by_digest) or any(
        by_digest[digest]["disposition"] != "active" for digest in current
    ):
        raise MaturityContractError("current evidence must be active")
    for digest, row in by_digest.items():
        target = row["superseded_by_sha256"]
        if target is not None:
            if target == digest or target not in by_digest:
                raise MaturityContractError("supersession target is missing or cyclic")
            seen = {digest}
            while target is not None:
                if target in seen:
                    raise MaturityContractError("supersession cycle")
                seen.add(target)
                target = by_digest[target]["superseded_by_sha256"]
    return sorted(lifecycle, key=lambda row: row["artifact_sha256"])


def build_maturity_candidate(
    *,
    context: VerifiedExecutionContext,
    reliability: dict[str, Any],
    extractor_metrics: dict[str, Any],
    thresholds: list[dict[str, Any]],
    evidence_lifecycle: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare registered thresholds and emit a packet that remains pending."""
    _require_capability(context)
    run_spec = context.run_spec
    reliability_sha = _artifact_pin(reliability, "reliability_sha256")
    extractor_sha = _artifact_pin(extractor_metrics, "extractor_metrics_sha256")
    _registered_artifact(run_spec, "reliability:", reliability_sha)
    _registered_artifact(run_spec, "extractor-metrics:", extractor_sha)
    _require_metric_pair_lineage(context, reliability, extractor_metrics)
    lifecycle = _validate_lifecycle(evidence_lifecycle, {reliability_sha, extractor_sha})
    artifacts = {"reliability": reliability, "extractor_metrics": extractor_metrics}
    results = []
    identities: set[str] = set()
    if not isinstance(thresholds, list):
        raise MaturityContractError("thresholds must be an array")
    for threshold in thresholds:
        if not isinstance(threshold, dict) or set(threshold) != {
            "threshold_id",
            "artifact",
            "metric_path",
            "operator",
            "value",
        }:
            raise MaturityContractError("threshold violates strict contract")
        threshold_id = threshold["threshold_id"]
        artifact_name = threshold["artifact"]
        operator = threshold["operator"]
        value = threshold["value"]
        if not isinstance(threshold_id, str) or not threshold_id or threshold_id in identities:
            raise MaturityContractError("threshold identities must be unique and nonempty")
        identities.add(threshold_id)
        if artifact_name not in artifacts or operator not in {">=", ">", "<=", "<", "=="}:
            raise MaturityContractError("threshold artifact or operator is unsupported")
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
        ):
            raise MaturityContractError("threshold value must be finite numeric")
        observed = _metric(artifacts[artifact_name], artifact_name, threshold["metric_path"])
        results.append(
            {
                **threshold,
                "value": float(value),
                "observed": observed,
                "threshold_eligible": True,
                "passed": _compare(observed, operator, float(value)),
            }
        )
    results.sort(key=lambda row: row["threshold_id"])
    candidate = seal_record(
        {
            "schema_version": "foio.australian-maturity-decision-candidate.v1.0.0",
            "status": "pending_human_decision",
            "run_id": run_spec.run_id,
            "run_spec_sha256": run_spec.run_spec_sha256,
            "membership_sha256": context.membership_sha256,
            "codebook_sha256": context.codebook_sha256,
            "population_sha256": context.population_sha256("maturity"),
            "authorization_artifact_sha256": context.authorization_artifact_sha256,
            "calibration_artifact_sha256": context.calibration_artifact_sha256,
            "reliability_sha256": reliability_sha,
            "extractor_metrics_sha256": extractor_sha,
            "source_metrics": {
                "reliability": reliability,
                "extractor_metrics": extractor_metrics,
            },
            "evidence_lifecycle": lifecycle,
            "threshold_results": results,
            "all_thresholds_satisfied": bool(results)
            and all(result["passed"] for result in results),
            "decision": None,
            "decision_authorized": False,
            "gold_promotion_authorized": False,
            "profile_promotion_authorized": False,
            "publication_authorized": False,
            "redistribution_authorized": False,
            "training_authorized": False,
            "legal_certification_authorized": False,
        },
        "candidate_sha256",
    )
    validate_maturity_candidate(candidate, context=context)
    return candidate


def validate_maturity_candidate(
    candidate: dict[str, Any],
    *,
    context: VerifiedExecutionContext | None = None,
) -> None:
    """Independently revalidate structure, pins, lifecycle, and threshold results."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(candidate),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise MaturityContractError("schema validation failed: " + errors[0].message)
    if candidate.get("candidate_sha256") != content_sha256(candidate, "candidate_sha256"):
        raise MaturityContractError("invalid maturity candidate self-pin")
    if context is not None:
        _require_capability(context)
        run_spec = context.run_spec
        expected = {
            "run_id": run_spec.run_id,
            "run_spec_sha256": run_spec.run_spec_sha256,
            "population_sha256": context.population_sha256("maturity"),
            "membership_sha256": context.membership_sha256,
            "codebook_sha256": context.codebook_sha256,
            "authorization_artifact_sha256": context.authorization_artifact_sha256,
            "calibration_artifact_sha256": context.calibration_artifact_sha256,
        }
        if any(candidate.get(field) != value for field, value in expected.items()):
            raise MaturityContractError("maturity candidate lineage differs from run")
    sources = candidate["source_metrics"]
    reliability_sha = _artifact_pin(sources["reliability"], "reliability_sha256")
    extractor_sha = _artifact_pin(sources["extractor_metrics"], "extractor_metrics_sha256")
    if context is not None:
        _registered_artifact(context.run_spec, "reliability:", reliability_sha)
        _registered_artifact(context.run_spec, "extractor-metrics:", extractor_sha)
    if (
        candidate["reliability_sha256"] != reliability_sha
        or candidate["extractor_metrics_sha256"] != extractor_sha
    ):
        raise MaturityContractError("source metric pin mismatch")
    if context is not None:
        _require_metric_pair_lineage(context, sources["reliability"], sources["extractor_metrics"])
    else:
        source = {
            field: sources["reliability"].get(field) for field in SOURCE_METRIC_LINEAGE_FIELDS
        }
        if any(sources["extractor_metrics"].get(field) != value for field, value in source.items()):
            raise MaturityContractError("registered metric artifacts do not share exact lineage")
        for field in LINEAGE_FIELDS[2:]:
            if source[field] != candidate[field]:
                raise MaturityContractError("source metric lineage differs from maturity candidate")
    _validate_lifecycle(candidate["evidence_lifecycle"], {reliability_sha, extractor_sha})
    artifacts = {
        "reliability": sources["reliability"],
        "extractor_metrics": sources["extractor_metrics"],
    }
    for result in candidate["threshold_results"]:
        observed = _metric(artifacts[result["artifact"]], result["artifact"], result["metric_path"])
        if result["threshold_eligible"] is not True:
            raise MaturityContractError("threshold targets a metric that is not eligible")
        if result["observed"] != observed or result["passed"] != _compare(
            observed, result["operator"], result["value"]
        ):
            raise MaturityContractError("threshold result differs from recomputation")
    expected = bool(candidate["threshold_results"]) and all(
        result["passed"] for result in candidate["threshold_results"]
    )
    if candidate["all_thresholds_satisfied"] != expected:
        raise MaturityContractError("aggregate threshold result differs from recomputation")
