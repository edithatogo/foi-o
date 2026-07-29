"""Shared descriptive reliability computation for Australian role reports."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

SEED = 20260721
REPLICATES = 10_000


def digest(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kappa(a: list[str], b: list[str]) -> tuple[float | None, str | None]:
    """Compute Cohen's kappa, preserving an explicit constant-marginal reason."""
    n = len(a)
    observed = sum(left == right for left, right in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in set(ca) | set(cb))
    if expected == 1:
        return None, "expected_agreement_equals_one"
    return (observed - expected) / (1 - expected), None


def interval(values: list[float]) -> dict[str, float]:
    """Return the registered percentile interval for bootstrap values."""
    values.sort()
    return {"lower": values[int(0.025 * len(values))], "upper": values[int(0.975 * len(values))]}


def compute_descriptive(
    *,
    report_path: Path,
    output_path: Path,
    expected_report_sha: str,
    expected_unit_count: int,
    annotation_prefix: str,
    schema: str,
    include_gold_and_profile_boundaries: bool = True,
) -> dict[str, Any]:
    """Compute shared descriptive statistics while preserving jurisdiction pins."""
    if digest(report_path) != expected_report_sha:
        raise ValueError("locked annotation report SHA-256 mismatch")
    root = report_path.parent
    a = json.loads(
        (root / f"{annotation_prefix}-annotator-a.annotations.json").read_text(encoding="utf-8")
    )
    b = json.loads(
        (root / f"{annotation_prefix}-annotator-b.annotations.json").read_text(encoding="utf-8")
    )
    if len(a) != len(b) or len(a) != expected_unit_count:
        raise ValueError("locked annotation sets do not match the approved unit count")
    labels_a, labels_b = [x["label"] for x in a], [x["label"] for x in b]
    raw_numerator = sum(x == y for x, y in zip(labels_a, labels_b, strict=True))
    raw = raw_numerator / len(a)
    kap, undefined = kappa(labels_a, labels_b)
    rng = random.Random(SEED)  # noqa: S311 - deterministic registered bootstrap seed
    raw_boot, kap_boot = [], []
    for _ in range(REPLICATES):
        picks = [rng.randrange(len(a)) for _ in a]
        sa, sb = [labels_a[i] for i in picks], [labels_b[i] for i in picks]
        raw_boot.append(sum(x == y for x, y in zip(sa, sb, strict=True)) / len(sa))
        kappa_value, _ = kappa(sa, sb)
        if kappa_value is not None:
            kap_boot.append(kappa_value)
    exact_span = sum(x["span"] == y["span"] for x, y in zip(a, b, strict=True))
    abstention = sum(x["abstention"] == y["abstention"] for x, y in zip(a, b, strict=True))
    value: dict[str, Any] = {
        "schema": schema,
        "status": "computed_descriptive_automated_not_threshold_decision",
        "locked_annotation_report_sha256": expected_report_sha,
        "unit_count": len(a),
        "calculation": {
            "bootstrap_seed": SEED,
            "replicates": REPLICATES,
            "cluster_unit": "singleton_duplicate_cluster",
        },
        "raw_label_agreement": {
            "numerator": raw_numerator,
            "denominator": len(a),
            "estimate": raw,
            "ci": interval(raw_boot),
        },
        "cohen_kappa": {
            "estimate": kap,
            "ci": interval(kap_boot) if kap_boot else None,
            "undefined_reason": undefined,
        },
        "exact_span_agreement": {
            "numerator": exact_span,
            "denominator": len(a),
            "estimate": exact_span / len(a),
        },
        "abstention_agreement": {
            "numerator": abstention,
            "denominator": len(a),
            "estimate": abstention / len(a),
        },
        "threshold_satisfaction_authorized": False,
        "extractor_metrics_authorized": False,
        "maturity_decision_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    if include_gold_and_profile_boundaries:
        value["gold_promotion_authorized"] = False
        value["profile_promotion_authorized"] = False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "reliability_sha256": digest(output_path)}
