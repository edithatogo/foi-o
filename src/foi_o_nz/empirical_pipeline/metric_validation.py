"""Independent structural and arithmetic validation for empirical metric artifacts."""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import content_sha256

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "json"
SCHEMAS = {
    "reliability": ("australian-empirical-reliability.schema.json", "reliability_sha256"),
    "extractor_metrics": (
        "australian-empirical-extractor-metrics.schema.json",
        "extractor_metrics_sha256",
    ),
}
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


class MetricArtifactError(ValueError):
    """Raised when a persisted metric artifact is not independently trustworthy."""


def _ratio(row: dict[str, Any], *, nullable: bool = False) -> None:
    numerator, denominator, estimate = row["numerator"], row["denominator"], row["estimate"]
    expected = numerator / denominator if denominator else None
    if denominator == 0 and not nullable:
        raise MetricArtifactError("metric denominator must be positive")
    if estimate != expected:
        raise MetricArtifactError("metric estimate differs from its exact counts")


def _lineage(artifact: dict[str, Any], expected_count: int) -> None:
    lineage = artifact["annotation_lineage"]
    roles = {row["role_id"] for row in lineage}
    packets = {row["packet_sha256"] for row in lineage}
    annotations = {row["annotation_set_sha256"] for row in lineage}
    if (
        len(roles) != expected_count
        or len(packets) != expected_count
        or len(annotations) != expected_count
    ):
        raise MetricArtifactError("metric annotation lineage is not distinct")
    declared = artifact.get("annotation_set_sha256")
    if declared is not None and sorted(declared) != sorted(annotations):
        raise MetricArtifactError("metric annotation-set registry differs from lineage")


def _kappa(
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


def _percentile(values: list[float], confidence: float) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    tail = (1 - confidence) / 2
    lower = max(0, min(len(ordered) - 1, math.floor(tail * len(ordered))))
    upper = max(0, min(len(ordered) - 1, math.ceil((1 - tail) * len(ordered)) - 1))
    return {"lower": ordered[lower], "upper": ordered[upper]}


def _bootstrap_indices(rows: list[dict[str, Any]], rng: random.Random) -> list[int]:
    clusters: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        clusters.setdefault(row["bootstrap_cluster_id"], []).append(index)
    cluster_ids = sorted(clusters)
    sampled = [cluster_ids[rng.randrange(len(cluster_ids))] for _ in cluster_ids]
    return [index for cluster_id in sampled for index in clusters[cluster_id]]


def _reliability(artifact: dict[str, Any]) -> None:
    unit_count = artifact["unit_count"]
    _lineage(artifact, 2)
    rows = artifact["agreement_rows"]
    if len(rows) != unit_count or len({row["unit_id"] for row in rows}) != unit_count:
        raise MetricArtifactError("reliability rows do not form the exact unit population")
    if rows != sorted(rows, key=lambda row: (row["unit_id"], row["unit_sha256"])):
        raise MetricArtifactError("reliability rows are not canonically ordered")
    bootstrap = artifact["bootstrap"]
    cluster_count = len({row["bootstrap_cluster_id"] for row in rows})
    if bootstrap["cluster_count"] != cluster_count:
        raise MetricArtifactError("bootstrap cluster count differs from row evidence")
    if bootstrap["unit"] == "singleton" and any(
        row["bootstrap_cluster_id"] != row["unit_id"] for row in rows
    ):
        raise MetricArtifactError("singleton bootstrap rows contain clustered identities")
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
    exact_counts = {
        "raw_label_agreement": (raw, unit_count),
        "all_unit_exact_span_agreement": (all_span, unit_count),
        "exact_span_agreement": (exact_span, len(eligible)),
        "abstention_agreement": (abstention, unit_count),
    }
    for name, (numerator, denominator) in exact_counts.items():
        if artifact[name]["numerator"] != numerator or artifact[name]["denominator"] != denominator:
            raise MetricArtifactError(f"{name} differs from row evidence")
    kappa, undefined_reason = _kappa(left_labels, right_labels)
    if (
        artifact["cohen_kappa"]["estimate"] != kappa
        or artifact["cohen_kappa"]["undefined_reason"] != undefined_reason
    ):
        raise MetricArtifactError("Cohen kappa differs from row evidence")
    for name in ("raw_label_agreement", "all_unit_exact_span_agreement", "abstention_agreement"):
        row = artifact[name]
        if row["denominator"] != unit_count:
            raise MetricArtifactError(f"{name} denominator differs from unit count")
        _ratio(row)
    exact = artifact["exact_span_agreement"]
    if exact["denominator"] > unit_count:
        raise MetricArtifactError("eligible span denominator exceeds unit count")
    _ratio(exact, nullable=True)
    replicates = artifact["bootstrap"]["replicates"]
    for row in (artifact["cohen_kappa"], exact):
        if row["bootstrap_replicates_valid"] + row["bootstrap_replicates_undefined"] != replicates:
            raise MetricArtifactError("bootstrap replicate accounting is inconsistent")
    kappa = artifact["cohen_kappa"]
    if (kappa["estimate"] is None) != (kappa["undefined_reason"] is not None):
        raise MetricArtifactError("kappa estimate and undefined reason are inconsistent")
    rng = random.Random(bootstrap["seed"])  # noqa: S311 - deterministic registered bootstrap
    raw_samples: list[float] = []
    kappa_samples: list[float] = []
    all_span_samples: list[float] = []
    exact_span_samples: list[float] = []
    abstention_samples: list[float] = []
    for _ in range(bootstrap["replicates"]):
        indices = _bootstrap_indices(rows, rng)
        sample_left = [left_labels[index] for index in indices]
        sample_right = [right_labels[index] for index in indices]
        raw_samples.append(
            sum(left == right for left, right in zip(sample_left, sample_right, strict=True))
            / len(indices)
        )
        sampled_kappa, _ = _kappa(sample_left, sample_right)
        if sampled_kappa is not None:
            kappa_samples.append(sampled_kappa)
        all_span_samples.append(
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
            exact_span_samples.append(
                sum(
                    rows[index]["left_spans_sha256"] == rows[index]["right_spans_sha256"]
                    for index in sampled_eligible
                )
                / len(sampled_eligible)
            )
        abstention_samples.append(
            sum((left_labels[index] is None) == (right_labels[index] is None) for index in indices)
            / len(indices)
        )
    expected_cis = {
        "raw_label_agreement": _percentile(raw_samples, bootstrap["confidence"]),
        "cohen_kappa": _percentile(kappa_samples, bootstrap["confidence"]),
        "all_unit_exact_span_agreement": _percentile(all_span_samples, bootstrap["confidence"]),
        "exact_span_agreement": _percentile(exact_span_samples, bootstrap["confidence"]),
        "abstention_agreement": _percentile(abstention_samples, bootstrap["confidence"]),
    }
    if any(artifact[name]["ci"] != ci for name, ci in expected_cis.items()):
        raise MetricArtifactError("bootstrap confidence interval differs from row evidence")
    if (
        kappa["bootstrap_replicates_valid"] != len(kappa_samples)
        or kappa["bootstrap_replicates_undefined"] != bootstrap["replicates"] - len(kappa_samples)
        or exact["bootstrap_replicates_valid"] != len(exact_span_samples)
        or exact["bootstrap_replicates_undefined"]
        != bootstrap["replicates"] - len(exact_span_samples)
    ):
        raise MetricArtifactError("bootstrap replicate counts differ from row evidence")


def _extractor(artifact: dict[str, Any]) -> None:
    unit_count = artifact["unit_count"]
    _lineage(artifact, 3)
    rows = artifact["confusion_rows"]
    if len(rows) != unit_count or len({row["unit_id"] for row in rows}) != unit_count:
        raise MetricArtifactError("extractor confusion rows do not form the exact unit population")
    tp = fp = fn = covered = eligible = exact = all_exact = 0
    for row in rows:
        label_match = row["predicted_label"] == row["reference_label"]
        span_eligible = row["predicted_label"] is not None and label_match
        if row["label_match"] != label_match or row["span_threshold_eligible"] != span_eligible:
            raise MetricArtifactError("extractor confusion row differs from recomputation")
        covered += int(row["predicted_label"] is not None)
        tp += int(span_eligible)
        fp += int(row["predicted_label"] is not None and not span_eligible)
        fn += int(row["reference_label"] is not None and not span_eligible)
        eligible += int(span_eligible)
        exact += int(span_eligible and row["exact_span_match"])
        all_exact += int(row["exact_span_match"])
    label = artifact["label_metrics"]
    expected_label = {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
    }
    precision, recall = expected_label["precision"], expected_label["recall"]
    expected_label["f1"] = (
        2 * precision * recall / (precision + recall) if precision + recall else 0.0
    )
    if label != expected_label:
        raise MetricArtifactError("extractor label metrics differ from confusion rows")
    if artifact["coverage"]["denominator"] != unit_count:
        raise MetricArtifactError("extractor coverage denominator differs from unit count")
    _ratio(artifact["coverage"])
    if artifact["coverage"]["numerator"] != covered:
        raise MetricArtifactError("extractor coverage differs from confusion rows")
    all_span = artifact["all_unit_exact_span"]
    if all_span["denominator"] != unit_count:
        raise MetricArtifactError("all-unit span denominator differs from unit count")
    _ratio(all_span)
    if all_span["numerator"] != all_exact:
        raise MetricArtifactError("all-unit span metric differs from confusion rows")
    conditioned = artifact["exact_span"]
    if conditioned["denominator"] != eligible or conditioned["numerator"] != exact:
        raise MetricArtifactError("eligible span metric differs from confusion rows")
    _ratio(conditioned, nullable=True)
    if artifact["span_iou"] is not None:
        if artifact["span_iou"]["denominator"] != eligible:
            raise MetricArtifactError("span IoU denominator differs from eligible rows")
        iou = {"numerator": artifact["span_iou"]["matched"], **artifact["span_iou"]}
        _ratio(iou, nullable=True)
        if artifact["span_iou"]["threshold_eligible"] is not False:
            raise MetricArtifactError("span IoU lacks independently recomputable row evidence")
    provenance = artifact["provenance_completeness"]
    if provenance["denominator"] != covered:
        raise MetricArtifactError("provenance denominator differs from covered predictions")
    _ratio(provenance, nullable=True)
    if provenance["threshold_eligible"] is not False:
        raise MetricArtifactError("provenance completeness lacks independently recomputable rows")


def validate_metric_artifact(artifact: dict[str, Any], kind: str) -> str:
    """Validate schema, self-pin, lineage registry, and independently recomputable metrics."""
    try:
        schema_name, pin_field = SCHEMAS[kind]
    except KeyError as error:
        raise MetricArtifactError("unsupported metric artifact kind") from error
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise MetricArtifactError("metric schema validation failed: " + errors[0].message)
    digest = artifact[pin_field]
    if digest != content_sha256(artifact, pin_field):
        raise MetricArtifactError(f"invalid {pin_field}")
    if any(
        isinstance(value, float) and not math.isfinite(value) for value in _numeric_values(artifact)
    ):
        raise MetricArtifactError("metric artifact contains a non-finite number")
    (_reliability if kind == "reliability" else _extractor)(artifact)
    return digest


def _numeric_values(value: Any) -> Iterator[int | float]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _numeric_values(item)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield value


def threshold_metric(artifact: dict[str, Any], kind: str, path: str) -> float:
    """Return only an explicitly registered threshold-eligible metric."""
    if path not in THRESHOLD_ELIGIBLE_METRICS.get(kind, frozenset()):
        raise MetricArtifactError("metric path is not eligible for registered thresholds")
    value: Any = artifact
    for component in path.split("."):
        if not isinstance(value, dict) or component not in value:
            raise MetricArtifactError(f"metric path not found: {path}")
        value = value[component]
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise MetricArtifactError(f"metric is not finite numeric: {path}")
    return float(value)
