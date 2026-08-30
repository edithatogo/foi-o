#!/usr/bin/env python3
"""Independently verify an Australian empirical stage execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "json"
AUTH_FIELDS = {
    "schema_version",
    "status",
    "authorization_id",
    "authorizer_kind",
    "authorizer_identity",
    "approval_artifact_sha256",
    "run_id",
    "run_spec_sha256",
    "stage_id",
    "stage_spec_sha256",
    "capability",
    "input_sha256",
    "output_sha256",
    "calibration_sha256",
    "authorization_sha256",
}
CALIBRATION_FIELDS = {
    "schema_version",
    "status",
    "run_id",
    "run_spec_sha256",
    "stage_id",
    "stage_spec_sha256",
    "capability",
    "approval_artifact_sha256",
    "calibrator_identity",
    "calibration_sha256",
}
MATURITY_LINEAGE_FIELDS = (
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "population_sha256",
    "authorization_artifact_sha256",
    "calibration_artifact_sha256",
)
THRESHOLD_ELIGIBLE_METRICS = {
    "reliability": frozenset({
        "raw_label_agreement.estimate",
        "cohen_kappa.estimate",
        "exact_span_agreement.estimate",
        "abstention_agreement.estimate",
    }),
    "extractor_metrics": frozenset({
        "label_metrics.precision",
        "label_metrics.recall",
        "label_metrics.f1",
        "coverage.estimate",
        "exact_span.estimate",
    }),
}


class OracleError(ValueError):
    """Raised when independent verification fails."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()


def _content_hash(value: dict[str, Any], self_pin: str) -> str:
    return hashlib.sha256(
        _canonical_bytes({key: item for key, item in value.items() if key != self_pin})
    ).hexdigest()


def _object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OracleError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise OracleError(f"{label} must be a JSON object")
    return value


def _git(repository: Path, *arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise OracleError("committed evidence cannot be verified") from exc


def _committed_run_spec(path: Path) -> Path:
    try:
        root = Path(
            subprocess.run(
                ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        ).resolve()
        resolved = path.resolve()
        relative = resolved.relative_to(root)
        committed = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:{relative.as_posix()}"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise OracleError("run specification is not a committed HEAD artifact") from exc
    if resolved.read_bytes() != committed:
        raise OracleError("run specification differs from its committed HEAD artifact")
    return root


def _evidence_sources(spec: dict[str, Any], repository: Path) -> None:
    for source in spec["evidence_sources"]:
        relative = Path(source["path"])
        current = (repository / relative).resolve()
        if not current.is_relative_to(repository) or not current.is_file():
            raise OracleError("evidence source path is outside or missing from repository")
        current_bytes = current.read_bytes()
        committed_bytes = _git(repository, "show", f"{source['git_commit']}:{relative.as_posix()}")
        for label, payload in (("current", current_bytes), ("committed", committed_bytes)):
            if len(payload) != source["size_bytes"]:
                raise OracleError(f"{label} evidence size differs from its pin")
            if hashlib.sha256(payload).hexdigest() != source["sha256"]:
                raise OracleError(f"{label} evidence hash differs from its pin")


def _schema(value: dict[str, Any], name: str) -> None:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise OracleError(f"{name} schema failure: {errors[0].message}")


def _file_hashes(paths: list[Path], label: str) -> list[str]:
    if not paths:
        raise OracleError(f"explicit {label} paths are required")
    try:
        hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    except OSError as exc:
        raise OracleError(f"cannot read {label} path") from exc
    if len(set(hashes)) != len(hashes):
        raise OracleError(f"duplicate {label} content")
    return hashes


def _registered_artifact(spec: dict[str, Any], prefix: str, digest: str) -> None:
    matches = [
        artifact
        for artifact in spec.get("referenced_artifacts", [])
        if str(artifact.get("artifact_id", "")).startswith(prefix)
        and artifact.get("sha256") == digest
    ]
    if len(matches) != 1:
        raise OracleError(f"{prefix.rstrip(':')} artifact is not uniquely registered")


def _canonical_unit(unit: dict[str, Any]) -> dict[str, Any]:
    if set(unit) not in (
        {"unit_id", "unit_sha256", "text"},
        {"unit_id", "unit_sha256", "text", "source_spans"},
    ):
        raise OracleError("source unit violates the strict field contract")
    normalized = {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
        "text": unit["text"],
        "source_spans": unit.get("source_spans", []),
    }
    preimage = {
        "unit_id": normalized["unit_id"],
        "text": normalized["text"],
        "source_spans": normalized["source_spans"],
    }
    if normalized["unit_sha256"] != hashlib.sha256(_canonical_bytes(preimage)).hexdigest():
        raise OracleError("source unit content hash mismatch")
    return normalized


def _approval_context(
    membership_sha256: str,
    codebook_sha256: str,
    source_bundle_sha256: str,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> str:
    calibration_content = {
        key: value
        for key, value in calibration.items()
        if key not in {"calibration_sha256", "external_approval", "run_spec_sha256"}
    }
    authorization_content = {
        key: value
        for key, value in authorization.items()
        if key
        not in {
            "authorization_sha256",
            "calibration_sha256",
            "external_approval",
            "run_spec_sha256",
        }
    }
    return hashlib.sha256(
        _canonical_bytes({
            "schema_version": "foio.empirical-approved-execution-context.v1.0.0",
            "membership_sha256": membership_sha256,
            "codebook_sha256": codebook_sha256,
            "source_bundle_sha256": source_bundle_sha256,
            "calibration_content_sha256": hashlib.sha256(
                _canonical_bytes(calibration_content)
            ).hexdigest(),
            "authorization_content_sha256": hashlib.sha256(
                _canonical_bytes(authorization_content)
            ).hexdigest(),
        })
    ).hexdigest()


def _verified_execution_context(
    *,
    spec: dict[str, Any],
    membership_path: Path,
    units_path: Path,
    codebook_path: Path,
    calibration_path: Path,
    authorization_path: Path,
    capability: str,
) -> None:
    membership = _object(membership_path, "membership")
    if (
        membership.get("membership_sha256") != _content_hash(membership, "membership_sha256")
        or membership.get("status") != "candidate_membership"
    ):
        raise OracleError("membership is not an exact candidate membership")
    membership_sha = membership["membership_sha256"]
    _registered_artifact(spec, "membership:", membership_sha)
    bundle = _object(units_path, "source bundle")
    raw_units = bundle.get("units")
    if not isinstance(raw_units, list) or not raw_units:
        raise OracleError("source bundle must contain units")
    units = sorted(
        (_canonical_unit(unit) for unit in raw_units),
        key=lambda row: (row["unit_id"], row["unit_sha256"]),
    )
    if len({unit["unit_id"] for unit in units}) != len(units):
        raise OracleError("source unit identities are duplicated")
    identities = [
        {"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]} for unit in units
    ]
    if membership.get("membership") != identities:
        raise OracleError("source bundle differs from membership")
    source_bundle_sha = hashlib.sha256(_canonical_bytes(units)).hexdigest()
    try:
        codebook_bytes = codebook_path.read_bytes()
        codebook = json.loads(codebook_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OracleError("codebook cannot be read") from exc
    codebook_sha = hashlib.sha256(codebook_bytes).hexdigest()
    _registered_artifact(spec, "codebook:", codebook_sha)
    labels = codebook.get("labels") if isinstance(codebook, dict) else None
    abstention = codebook.get("abstention") if isinstance(codebook, dict) else None
    if (
        not isinstance(labels, list)
        or not labels
        or not isinstance(abstention, dict)
        or not (abstention.get("reasons"))
    ):
        raise OracleError("codebook has no executable vocabulary")
    calibration = _object(calibration_path, "calibration")
    authorization = _object(authorization_path, "authorization")
    _schema(calibration, "australian-empirical-calibration-result.schema.json")
    _schema(authorization, "australian-empirical-execution-authorization.schema.json")
    if calibration["calibration_sha256"] != _content_hash(
        calibration, "calibration_sha256"
    ) or authorization["authorization_sha256"] != _content_hash(
        authorization, "authorization_sha256"
    ):
        raise OracleError("execution authority self-pin is invalid")
    expected = {
        "run_spec_sha256": spec["run_spec_sha256"],
        "membership_sha256": membership_sha,
        "codebook_sha256": codebook_sha,
    }
    if any(calibration.get(field) != value for field, value in expected.items()) or any(
        authorization.get(field) != value for field, value in expected.items()
    ):
        raise OracleError("execution authority lineage differs")
    if authorization.get("calibration_sha256") != calibration["calibration_sha256"]:
        raise OracleError("authorization calibration binding differs")
    if set(calibration["role_ids"]) != set(authorization["approved_roles"]):
        raise OracleError("execution authority roles differ")
    if capability not in authorization["capabilities"]:
        raise OracleError("capability is absent from external authorization")
    approved_context = _approval_context(
        membership_sha, codebook_sha, source_bundle_sha, calibration, authorization
    )
    bindings = spec.get("authority_bindings")
    if not isinstance(bindings, dict):
        raise OracleError("run authority bindings are missing")
    pairs = (
        (calibration["external_approval"], bindings["calibration_approval"]),
        (
            authorization["external_approval"],
            bindings["execution_authorization_approval"],
        ),
    )
    for artifact, binding in pairs:
        if artifact.get("artifact_sha256") != _content_hash(artifact, "artifact_sha256"):
            raise OracleError("external approval self-pin is invalid")
        if artifact != binding or artifact["approved_context_sha256"] != approved_context:
            raise OracleError("external approval differs from immutable run binding")
        _registered_artifact(spec, "approval:", artifact["artifact_sha256"])


def _stage(spec: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    stages = spec["stages"]
    sequences = sorted(stage["sequence"] for stage in stages)
    if sequences != list(range(1, len(stages) + 1)):
        raise OracleError("stage order is not contiguous")
    matches = [stage for stage in stages if stage["stage_id"] == result["stage_id"]]
    if len(matches) != 1:
        raise OracleError("stage result does not identify exactly one stage")
    return matches[0]


def _population(value: dict[str, Any]) -> None:
    if value["predecessor"] != value["included"] + value["excluded"] + value["unresolved"]:
        raise OracleError("population conservation failed")


def _executable_lifecycle(spec: dict[str, Any]) -> None:
    allowed = {
        "active": {"active", "opaque_producer"},
        "candidate": {"active", "opaque_producer"},
        "superseded": {"superseded"},
        "invalidated": {"invalidated"},
    }
    assessment = spec.get("assessment_status")
    disposition = spec.get("lifecycle_disposition")
    if assessment not in allowed or disposition not in allowed[assessment]:
        raise OracleError("assessment status and lifecycle disposition are incompatible")
    if assessment in {"superseded", "invalidated"} or disposition in {
        "superseded",
        "invalidated",
    }:
        raise OracleError("retired empirical run cannot execute stages")
    relationships = spec.get("relationships")
    if not isinstance(relationships, dict):
        raise OracleError("run relationships are missing")
    run_id = spec.get("run_id")
    supersedes = set(relationships.get("supersedes", []))
    invalidates = set(relationships.get("invalidates", []))
    if run_id in supersedes or run_id in invalidates:
        raise OracleError("run relationship cannot contain a self-reference")
    if supersedes & invalidates:
        raise OracleError("supersedes and invalidates relationships overlap")


def _registered_approval(spec: dict[str, Any], prefix: str, digest: object) -> None:
    matches = [
        artifact
        for artifact in spec.get("referenced_artifacts", [])
        if artifact.get("artifact_id", "").startswith(prefix) and artifact.get("sha256") == digest
    ]
    if len(matches) != 1:
        raise OracleError(f"{prefix.rstrip(':')} approval artifact is not uniquely registered")


def _prior(paths: list[Path], spec: dict[str, Any], stage: dict[str, Any]) -> None:
    expected = sorted(
        (item for item in spec["stages"] if item["sequence"] < stage["sequence"]),
        key=lambda item: item["sequence"],
    )
    if len(paths) != len(expected):
        raise OracleError("prior stage results are missing or excessive")
    for path, expected_stage in zip(paths, expected, strict=True):
        prior = _object(path, "prior stage result")
        _schema(prior, "australian-empirical-stage-result.schema.json")
        if prior["stage_result_sha256"] != _content_hash(prior, "stage_result_sha256"):
            raise OracleError("prior stage result hash is invalid")
        stage_pin = hashlib.sha256(_canonical_bytes(expected_stage)).hexdigest()
        expected_fields = {
            "stage_spec_sha256": stage_pin,
            "input_sha256": expected_stage["input_sha256"],
            "output_sha256": expected_stage["output_sha256"],
            "population": expected_stage["population"],
            "allowed_capabilities": expected_stage["allowed_capabilities"],
            "denied_capabilities": expected_stage["denied_capabilities"],
        }
        if (
            prior["run_spec_sha256"] != spec["run_spec_sha256"]
            or prior["stage_id"] != expected_stage["stage_id"]
            or prior["stage_sequence"] != expected_stage["sequence"]
            or prior["result_status"] != "completed"
            or any(prior[key] != value for key, value in expected_fields.items())
        ):
            raise OracleError("prior stage result is incomplete or out of order")


def _authorization(
    path: Path,
    spec: dict[str, Any],
    stage: dict[str, Any],
    capability: str,
    calibration: dict[str, Any] | None,
) -> None:
    value = _object(path, "authorization")
    if set(value) != AUTH_FIELDS or value["authorization_sha256"] != _content_hash(
        value, "authorization_sha256"
    ):
        raise OracleError("authorization structure or hash is invalid")
    stage_pin = hashlib.sha256(_canonical_bytes(stage)).hexdigest()
    expected = {
        "schema_version": "foio.empirical-stage-authorization.v1.0.0",
        "status": "approved",
        "authorizer_kind": "external_human",
        "run_id": spec["run_id"],
        "run_spec_sha256": spec["run_spec_sha256"],
        "stage_id": stage["stage_id"],
        "stage_spec_sha256": stage_pin,
        "capability": capability,
        "input_sha256": stage["input_sha256"],
        "output_sha256": stage["output_sha256"],
        "calibration_sha256": (
            calibration["calibration_sha256"] if calibration is not None else None
        ),
    }
    if any(value[key] != expected_value for key, expected_value in expected.items()):
        raise OracleError("authorization is not externally bound to this execution")
    identity = value["authorizer_identity"]
    if (
        not isinstance(identity, dict)
        or set(identity) != {"identity_id", "identity_kind"}
        or identity.get("identity_kind") != "external_human"
        or not isinstance(identity.get("identity_id"), str)
        or not identity["identity_id"]
    ):
        raise OracleError("authorization identity is not an external human")
    _registered_approval(spec, "authorization:", value["approval_artifact_sha256"])
    if (
        not isinstance(value["authorization_id"], str)
        or not value["authorization_id"].startswith("authorization:external-human:")
        or value["authorization_id"] in {spec["run_id"], stage["stage_id"]}
        or value["authorization_sha256"] in {*stage["input_sha256"], *stage["output_sha256"]}
    ):
        raise OracleError("self-authorization is forbidden")


def _calibration(
    path: Path | None, spec: dict[str, Any], stage: dict[str, Any], capability: str
) -> dict[str, Any] | None:
    governed = stage["stage_kind"] in {"packet", "annotation", "maturity"}
    if governed and path is None:
        raise OracleError("passed calibration is required")
    if path is None:
        return None
    value = _object(path, "calibration")
    if set(value) != CALIBRATION_FIELDS or value["calibration_sha256"] != _content_hash(
        value, "calibration_sha256"
    ):
        raise OracleError("calibration structure or hash is invalid")
    _registered_approval(spec, "calibration:", value["approval_artifact_sha256"])
    identity = value["calibrator_identity"]
    if (
        not isinstance(identity, dict)
        or set(identity) != {"identity_id", "identity_kind"}
        or identity.get("identity_kind") not in {"external_human", "automated_calibration_harness"}
        or not isinstance(identity.get("identity_id"), str)
        or not identity["identity_id"]
    ):
        raise OracleError("calibration identity is invalid")
    expected = {
        "schema_version": "foio.empirical-stage-calibration.v1.0.0",
        "status": "passed",
        "run_id": spec["run_id"],
        "run_spec_sha256": spec["run_spec_sha256"],
        "stage_id": stage["stage_id"],
        "stage_spec_sha256": hashlib.sha256(_canonical_bytes(stage)).hexdigest(),
        "capability": capability,
    }
    if any(value[key] != expected_value for key, expected_value in expected.items()):
        raise OracleError("calibration is not passed and bound to this execution")
    return value


def _ratio(value: dict[str, Any], *, nullable: bool = False) -> None:
    denominator = value["denominator"]
    expected = value["numerator"] / denominator if denominator else None
    if denominator == 0 and not nullable:
        raise OracleError("metric denominator must be positive")
    if value["estimate"] != expected:
        raise OracleError("metric estimate differs from its exact counts")


def _metric_lineage(value: dict[str, Any], expected_count: int) -> None:
    lineage = value["annotation_lineage"]
    if (
        len({row["role_id"] for row in lineage}) != expected_count
        or len({row["packet_sha256"] for row in lineage}) != expected_count
        or len({row["annotation_set_sha256"] for row in lineage}) != expected_count
    ):
        raise OracleError("metric annotation lineage is not distinct")
    declared = value.get("annotation_set_sha256")
    if declared is not None and sorted(declared) != sorted(
        row["annotation_set_sha256"] for row in lineage
    ):
        raise OracleError("metric annotation-set registry differs from lineage")


def _oracle_kappa(
    left_labels: list[str | None], right_labels: list[str | None]
) -> tuple[float | None, str | None]:
    count = len(left_labels)
    observed = (
        sum(left == right for left, right in zip(left_labels, right_labels, strict=True)) / count
    )
    left_counts, right_counts = Counter(left_labels), Counter(right_labels)
    expected = sum(
        (left_counts[label] / count) * (right_counts[label] / count)
        for label in set(left_counts) | set(right_counts)
    )
    if math.isclose(expected, 1.0, abs_tol=1e-15):
        return None, "expected_agreement_equals_one"
    return (observed - expected) / (1 - expected), None


def _oracle_percentile(values: list[float], confidence: float) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    tail = (1 - confidence) / 2
    lower = max(0, min(len(ordered) - 1, math.floor(tail * len(ordered))))
    upper = max(0, min(len(ordered) - 1, math.ceil((1 - tail) * len(ordered)) - 1))
    return {"lower": ordered[lower], "upper": ordered[upper]}


def _oracle_bootstrap_indices(rows: list[dict[str, Any]], rng: random.Random) -> list[int]:
    clusters: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        clusters.setdefault(row["bootstrap_cluster_id"], []).append(index)
    cluster_ids = sorted(clusters)
    sampled = [cluster_ids[rng.randrange(len(cluster_ids))] for _ in cluster_ids]
    return [index for cluster_id in sampled for index in clusters[cluster_id]]


def _verify_reliability_arithmetic(value: dict[str, Any]) -> None:
    unit_count = value["unit_count"]
    _metric_lineage(value, 2)
    rows = value["agreement_rows"]
    if (
        len(rows) != unit_count
        or len({row["unit_id"] for row in rows}) != unit_count
        or rows != sorted(rows, key=lambda row: (row["unit_id"], row["unit_sha256"]))
    ):
        raise OracleError("reliability rows differ from the exact canonical population")
    bootstrap = value["bootstrap"]
    if bootstrap["cluster_count"] != len({row["bootstrap_cluster_id"] for row in rows}):
        raise OracleError("bootstrap cluster count differs from row evidence")
    if bootstrap["unit"] == "singleton" and any(
        row["bootstrap_cluster_id"] != row["unit_id"] for row in rows
    ):
        raise OracleError("singleton bootstrap contains clustered rows")
    left_labels = [row["left_label"] for row in rows]
    right_labels = [row["right_label"] for row in rows]
    raw = sum(left == right for left, right in zip(left_labels, right_labels, strict=True))
    all_span = sum(row["left_spans_sha256"] == row["right_spans_sha256"] for row in rows)
    eligible = [
        index
        for index, (left, right) in enumerate(zip(left_labels, right_labels, strict=True))
        if left is not None and left == right
    ]
    exact_span = sum(
        rows[index]["left_spans_sha256"] == rows[index]["right_spans_sha256"] for index in eligible
    )
    abstention = sum(
        (left is None) == (right is None)
        for left, right in zip(left_labels, right_labels, strict=True)
    )
    for name, expected in {
        "raw_label_agreement": (raw, unit_count),
        "all_unit_exact_span_agreement": (all_span, unit_count),
        "exact_span_agreement": (exact_span, len(eligible)),
        "abstention_agreement": (abstention, unit_count),
    }.items():
        if (value[name]["numerator"], value[name]["denominator"]) != expected:
            raise OracleError(f"{name} differs from row evidence")
        _ratio(value[name], nullable=name == "exact_span_agreement")
    kappa, undefined_reason = _oracle_kappa(left_labels, right_labels)
    if (
        value["cohen_kappa"]["estimate"] != kappa
        or value["cohen_kappa"]["undefined_reason"] != undefined_reason
    ):
        raise OracleError("Cohen kappa differs from row evidence")
    rng = random.Random(bootstrap["seed"])  # noqa: S311 - deterministic registered bootstrap
    samples: dict[str, list[float]] = {
        "raw_label_agreement": [],
        "cohen_kappa": [],
        "all_unit_exact_span_agreement": [],
        "exact_span_agreement": [],
        "abstention_agreement": [],
    }
    for _ in range(bootstrap["replicates"]):
        indices = _oracle_bootstrap_indices(rows, rng)
        sample_left = [left_labels[index] for index in indices]
        sample_right = [right_labels[index] for index in indices]
        samples["raw_label_agreement"].append(
            sum(left == right for left, right in zip(sample_left, sample_right, strict=True))
            / len(indices)
        )
        sampled_kappa, _ = _oracle_kappa(sample_left, sample_right)
        if sampled_kappa is not None:
            samples["cohen_kappa"].append(sampled_kappa)
        samples["all_unit_exact_span_agreement"].append(
            sum(
                rows[index]["left_spans_sha256"] == rows[index]["right_spans_sha256"]
                for index in indices
            )
            / len(indices)
        )
        sampled_eligible = [
            index
            for index in indices
            if left_labels[index] is not None and left_labels[index] == right_labels[index]
        ]
        if sampled_eligible:
            samples["exact_span_agreement"].append(
                sum(
                    rows[index]["left_spans_sha256"] == rows[index]["right_spans_sha256"]
                    for index in sampled_eligible
                )
                / len(sampled_eligible)
            )
        samples["abstention_agreement"].append(
            sum((left_labels[index] is None) == (right_labels[index] is None) for index in indices)
            / len(indices)
        )
    for name, observed in samples.items():
        if value[name]["ci"] != _oracle_percentile(observed, bootstrap["confidence"]):
            raise OracleError("bootstrap confidence interval differs from row evidence")
    kappa_row = value["cohen_kappa"]
    exact_row = value["exact_span_agreement"]
    if (
        kappa_row["bootstrap_replicates_valid"] != len(samples["cohen_kappa"])
        or kappa_row["bootstrap_replicates_undefined"]
        != bootstrap["replicates"] - len(samples["cohen_kappa"])
        or exact_row["bootstrap_replicates_valid"] != len(samples["exact_span_agreement"])
        or exact_row["bootstrap_replicates_undefined"]
        != bootstrap["replicates"] - len(samples["exact_span_agreement"])
    ):
        raise OracleError("bootstrap replicate counts differ from row evidence")


def _maturity_artifact(value: dict[str, Any], pin: str, kind: str) -> str:
    schema = (
        "australian-empirical-reliability.schema.json"
        if kind == "reliability"
        else "australian-empirical-extractor-metrics.schema.json"
    )
    _schema(value, schema)
    digest = value.get(pin)
    if not isinstance(digest, str) or digest != _content_hash(value, pin):
        raise OracleError(f"maturity source metric has invalid {pin}")
    unit_count = value["unit_count"]
    if kind == "reliability":
        _verify_reliability_arithmetic(value)
    else:
        _metric_lineage(value, 3)
        rows = value["confusion_rows"]
        if len(rows) != unit_count or len({row["unit_id"] for row in rows}) != unit_count:
            raise OracleError("extractor confusion rows differ from exact population")
        tp = fp = fn = covered = eligible = exact = 0
        for row in rows:
            label_match = row["predicted_label"] == row["reference_label"]
            span_eligible = row["predicted_label"] is not None and label_match
            if row["label_match"] != label_match or row["span_threshold_eligible"] != span_eligible:
                raise OracleError("extractor confusion row differs from recomputation")
            covered += int(row["predicted_label"] is not None)
            tp += int(span_eligible)
            fp += int(row["predicted_label"] is not None and not span_eligible)
            fn += int(row["reference_label"] is not None and not span_eligible)
            eligible += int(span_eligible)
            exact += int(span_eligible and row["exact_span_match"])
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        expected_label = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        }
        if value["label_metrics"] != expected_label:
            raise OracleError("extractor label metrics differ from confusion rows")
        if value["coverage"]["denominator"] != unit_count:
            raise OracleError("extractor coverage denominator differs from unit count")
        _ratio(value["coverage"])
        if value["coverage"]["numerator"] != covered:
            raise OracleError("extractor coverage differs from confusion rows")
        if (
            value["exact_span"]["denominator"] != eligible
            or value["exact_span"]["numerator"] != exact
        ):
            raise OracleError("extractor span metric differs from confusion rows")
        _ratio(value["exact_span"], nullable=True)
        if value["all_unit_exact_span"]["denominator"] != unit_count:
            raise OracleError("all-unit span denominator differs from unit count")
        _ratio(value["all_unit_exact_span"])
        if value["all_unit_exact_span"]["numerator"] != sum(
            int(row["exact_span_match"]) for row in rows
        ):
            raise OracleError("all-unit span metric differs from confusion rows")
        if value["span_iou"] is not None:
            if value["span_iou"]["threshold_eligible"] is not False:
                raise OracleError("span IoU is not independently threshold eligible")
            _ratio(
                {"numerator": value["span_iou"]["matched"], **value["span_iou"]},
                nullable=True,
            )
        if value["provenance_completeness"]["threshold_eligible"] is not False:
            raise OracleError("provenance completeness is not independently threshold eligible")
        _ratio(value["provenance_completeness"], nullable=True)
    return digest


def _maturity_metric(root: dict[str, Any], kind: str, path: str) -> float:
    if path not in THRESHOLD_ELIGIBLE_METRICS.get(kind, frozenset()):
        raise OracleError("maturity metric path is not eligible for registered thresholds")
    value: Any = root
    for component in path.split("."):
        if not component or not isinstance(value, dict) or component not in value:
            raise OracleError(f"maturity metric path is missing: {path}")
        value = value[component]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise OracleError(f"maturity metric is not numeric: {path}")
    observed = float(value)
    if not (-float("inf") < observed < float("inf")):
        raise OracleError(f"maturity metric is not finite: {path}")
    return observed


def _maturity_compare(observed: float, operator: str, threshold: float) -> bool:
    comparisons = {
        ">=": observed >= threshold,
        ">": observed > threshold,
        "<=": observed <= threshold,
        "<": observed < threshold,
        "==": observed == threshold,
    }
    try:
        return comparisons[operator]
    except KeyError as exc:
        raise OracleError("maturity threshold operator is unsupported") from exc


def _maturity_lifecycle(rows: list[dict[str, Any]], current: set[str]) -> None:
    by_digest: dict[str, dict[str, Any]] = {}
    for row in rows:
        digest = row["artifact_sha256"]
        if digest in by_digest:
            raise OracleError("maturity lifecycle contains duplicate identities")
        by_digest[digest] = row
        disposition = row["disposition"]
        successor = row["superseded_by_sha256"]
        reason = row["reason"]
        if disposition == "active" and (successor is not None or reason is not None):
            raise OracleError("active maturity evidence carries retirement metadata")
        if disposition == "superseded" and (
            not isinstance(successor, str) or not isinstance(reason, str) or not reason
        ):
            raise OracleError("superseded maturity evidence lacks successor or reason")
        if disposition == "invalidated" and (
            successor is not None or not isinstance(reason, str) or not reason
        ):
            raise OracleError("invalidated maturity evidence has invalid metadata")
    if not current <= set(by_digest) or any(
        by_digest[digest]["disposition"] != "active" for digest in current
    ):
        raise OracleError("current maturity evidence is not active")
    for digest, row in by_digest.items():
        target = row["superseded_by_sha256"]
        seen = {digest}
        while target is not None:
            if target in seen or target not in by_digest:
                raise OracleError("maturity evidence supersession is cyclic or missing")
            seen.add(target)
            target = by_digest[target]["superseded_by_sha256"]


def _maturity(paths: list[Path], stage: dict[str, Any], spec: dict[str, Any]) -> None:
    if stage["stage_kind"] != "maturity":
        return
    if len(paths) != 1:
        raise OracleError("exactly one maturity candidate output is required")
    for path in paths:
        value = _object(path, "maturity output")
        _schema(value, "australian-maturity-decision-candidate.schema.json")
        if value["candidate_sha256"] != _content_hash(value, "candidate_sha256"):
            raise OracleError("maturity candidate self-pin is invalid")
        expected = {
            "run_id": spec["run_id"],
            "run_spec_sha256": spec["run_spec_sha256"],
            "population_sha256": stage["population"]["population_sha256"],
        }
        if any(value[field] != expected_value for field, expected_value in expected.items()):
            raise OracleError("maturity candidate lineage differs from the run")
        for prefix, field in (
            ("membership:", "membership_sha256"),
            ("codebook:", "codebook_sha256"),
            ("approval:", "authorization_artifact_sha256"),
            ("approval:", "calibration_artifact_sha256"),
        ):
            _registered_approval(spec, prefix, value[field])
        sources = value["source_metrics"]
        reliability_sha = _maturity_artifact(
            sources["reliability"], "reliability_sha256", "reliability"
        )
        extractor_sha = _maturity_artifact(
            sources["extractor_metrics"], "extractor_metrics_sha256", "extractor_metrics"
        )
        _registered_approval(spec, "reliability:", reliability_sha)
        _registered_approval(spec, "extractor-metrics:", extractor_sha)
        if (
            value["reliability_sha256"] != reliability_sha
            or value["extractor_metrics_sha256"] != extractor_sha
        ):
            raise OracleError("maturity source metric pin mismatch")
        source_lineage = {
            field: sources["reliability"].get(field) for field in MATURITY_LINEAGE_FIELDS
        }
        if any(
            sources["extractor_metrics"].get(field) != pin for field, pin in source_lineage.items()
        ):
            raise OracleError("registered metric artifacts do not share exact lineage")
        for field in MATURITY_LINEAGE_FIELDS[2:]:
            if source_lineage[field] != value[field]:
                raise OracleError("maturity source metric lineage mismatch")
        _maturity_lifecycle(value["evidence_lifecycle"], {reliability_sha, extractor_sha})
        artifacts = {
            "reliability": sources["reliability"],
            "extractor_metrics": sources["extractor_metrics"],
        }
        identities: set[str] = set()
        for result in value["threshold_results"]:
            if result["threshold_id"] in identities:
                raise OracleError("maturity threshold identity is duplicated")
            identities.add(result["threshold_id"])
            observed = _maturity_metric(
                artifacts[result["artifact"]], result["artifact"], result["metric_path"]
            )
            passed = _maturity_compare(observed, result["operator"], result["value"])
            if result["threshold_eligible"] is not True:
                raise OracleError("maturity threshold targets an ineligible metric")
            if result["observed"] != observed or result["passed"] != passed:
                raise OracleError("maturity threshold result differs from recomputation")
        aggregate = bool(value["threshold_results"]) and all(
            result["passed"] for result in value["threshold_results"]
        )
        if value["all_thresholds_satisfied"] != aggregate:
            raise OracleError("maturity aggregate differs from recomputation")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--units", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--stage-result", type=Path, required=True)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--prior-result", type=Path, action="append", default=[])
    return parser


def main() -> int:
    """Run independent, fail-closed verification."""
    args = _parser().parse_args()
    try:
        governed_paths = {
            args.run_spec.resolve(),
            args.stage_result.resolve(),
            args.authorization.resolve(),
            args.calibration.resolve(),
            args.membership.resolve(),
            args.units.resolve(),
            args.codebook.resolve(),
        }
        data_paths = {
            *(path.resolve() for path in args.input),
            *(path.resolve() for path in args.output),
            *(path.resolve() for path in args.prior_result),
        }
        expected_governed_count = 7
        if len(governed_paths) != expected_governed_count or governed_paths & data_paths:
            raise OracleError("governance, result, and empirical evidence paths must be distinct")
        repository = _committed_run_spec(args.run_spec)
        spec = _object(args.run_spec, "run specification")
        result = _object(args.stage_result, "stage result")
        _schema(spec, "australian-empirical-run-spec.schema.json")
        _schema(result, "australian-empirical-stage-result.schema.json")
        if spec["run_spec_sha256"] != _content_hash(spec, "run_spec_sha256"):
            raise OracleError("run specification hash is invalid")
        _executable_lifecycle(spec)
        _evidence_sources(spec, repository)
        _verified_execution_context(
            spec=spec,
            membership_path=args.membership,
            units_path=args.units,
            codebook_path=args.codebook,
            calibration_path=args.calibration,
            authorization_path=args.authorization,
            capability=args.capability,
        )
        if result["stage_result_sha256"] != _content_hash(result, "stage_result_sha256"):
            raise OracleError("stage result hash is invalid")
        stage = _stage(spec, result)
        _population(stage["population"])
        _population(result["population"])
        if (
            args.capability not in stage["allowed_capabilities"]
            or args.capability in stage["denied_capabilities"]
        ):
            raise OracleError("capability is not allowed")
        stage_pin = hashlib.sha256(_canonical_bytes(stage)).hexdigest()
        expected = {
            "run_id": spec["run_id"],
            "run_spec_sha256": spec["run_spec_sha256"],
            "stage_sequence": stage["sequence"],
            "stage_spec_sha256": stage_pin,
            "input_sha256": stage["input_sha256"],
            "output_sha256": stage["output_sha256"],
            "population": stage["population"],
            "allowed_capabilities": stage["allowed_capabilities"],
            "denied_capabilities": stage["denied_capabilities"],
        }
        if result["result_status"] != "completed" or any(
            result[key] != expected_value for key, expected_value in expected.items()
        ):
            raise OracleError("stage result differs from immutable stage contract")
        if _file_hashes(args.input, "input") != stage["input_sha256"]:
            raise OracleError("input hashes differ from immutable pins")
        if stage["stage_kind"] != "maturity" and (
            _file_hashes(args.output, "output") != stage["output_sha256"]
        ):
            raise OracleError("output hashes differ from immutable pins")
        _prior(args.prior_result, spec, stage)
        _maturity(args.output, stage, spec)
    except OracleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "stage_result_sha256": result["stage_result_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
