"""Compute the approved descriptive reliability report for locked AU-CTH roles."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

REPORT_SHA = "22f5850badf02b0730f30fb1221bcc9fa7f6e74ac46338755a6e777eaff1db32"
SEED = 20260721


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kappa(a: list[str], b: list[str]) -> tuple[float | None, str | None]:
    n = len(a)
    observed = sum(left == right for left, right in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in set(ca) | set(cb))
    if expected == 1:
        return None, "expected_agreement_equals_one"
    return (observed - expected) / (1 - expected), None


def interval(values: list[float]) -> dict[str, float]:
    values.sort()
    return {"lower": values[int(0.025 * len(values))], "upper": values[int(0.975 * len(values))]}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--report", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if digest(args.report) != REPORT_SHA:
    raise SystemExit("ERROR: locked annotation report SHA-256 mismatch")
root = args.report.parent
a = json.loads((root / "au-cth-annotator-a.annotations.json").read_text())
b = json.loads((root / "au-cth-annotator-b.annotations.json").read_text())
if len(a) != len(b) or len(a) != 385:
    raise SystemExit("ERROR: locked annotation sets are not the approved 385 pairs")
labels_a, labels_b = [x["label"] for x in a], [x["label"] for x in b]
raw = sum(x == y for x, y in zip(labels_a, labels_b, strict=True)) / len(a)
kap, undefined = kappa(labels_a, labels_b)
rng = random.Random(SEED)  # noqa: S311 - deterministic registered bootstrap seed
raw_boot, kap_boot = [], []
for _ in range(10_000):
    picks = [rng.randrange(len(a)) for _ in a]
    sa, sb = [labels_a[i] for i in picks], [labels_b[i] for i in picks]
    raw_boot.append(sum(x == y for x, y in zip(sa, sb, strict=True)) / len(sa))
    value, _ = kappa(sa, sb)
    if value is not None:
        kap_boot.append(value)
exact_span = sum(x["span"] == y["span"] for x, y in zip(a, b, strict=True))
abstention = sum(x["abstention"] == y["abstention"] for x, y in zip(a, b, strict=True))
value = {
    "schema": "foi-o.au-cth-subset-descriptive-reliability.v1",
    "status": "computed_descriptive_automated_not_threshold_decision",
    "locked_annotation_report_sha256": REPORT_SHA,
    "unit_count": len(a),
    "calculation": {
        "bootstrap_seed": SEED,
        "replicates": 10000,
        "cluster_unit": "singleton_duplicate_cluster",
    },
    "raw_label_agreement": {
        "numerator": int(raw * len(a)),
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
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"ok": True, "reliability_sha256": digest(args.output)}, sort_keys=True))
