"""Compute bounded descriptive metrics for the AU-NSW candidate extractor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from foi_o_nz.australian_nsw_extractor import extract_assertion

REPORT_SHA = "c783713789b33cdd3eb25e4cd5b374f0c609fb63c6b4728bf0cf933eed54dd82"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.report) != REPORT_SHA:
        raise SystemExit("ERROR: locked v3 report SHA-256 mismatch")
    root = args.report.parent
    a = json.loads((root / "au-nsw-annotator-a.annotations.json").read_text())
    b = json.loads((root / "au-nsw-annotator-b.annotations.json").read_text())
    adjudications = {x["unit_id"]: x for x in json.loads((root / "adjudications.json").read_text())}
    reference = {}
    for left, _right in zip(a, b, strict=True):
        reference[left["unit_id"]] = adjudications.get(
            left["unit_id"], {"label": left["label"], "span": left["span"]}
        )
    frame_path = Path(
        "/Volumes/PortableSSD/foio-restricted/au-rtk-30236042144/au-nsw-immutable-frame/frame.json"
    )
    frame = {x["unit_id"]: x for x in json.loads(frame_path.read_text())["units"]}
    rows = []
    for unit_id, expected in reference.items():
        actual = extract_assertion(frame[unit_id]["text"])
        rows.append(
            {
                "unit_id": unit_id,
                "reference_label": expected["label"],
                "extractor_label": actual["label"],
                "reference_span": expected.get("span"),
                "extractor_span": actual["span"],
                "label_match": actual["label"] == expected["label"],
                "span_match": actual["span"] == expected.get("span"),
            }
        )
    output = {
        "schema": "foi-o.au-nsw-extractor-metrics.v1",
        "status": "descriptive_candidate_not_mature",
        "annotation_report_sha256": REPORT_SHA,
        "unit_count": len(rows),
        "label_accuracy": sum(x["label_match"] for x in rows) / len(rows),
        "span_exact_accuracy": sum(x["span_match"] for x in rows) / len(rows),
        "label_disagreement_count": sum(not x["label_match"] for x in rows),
        "span_disagreement_count": sum(not x["span_match"] for x in rows),
        "rows": rows,
        "gold_promotion_authorized": False,
        "profile_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"ok": True, "metrics_sha256": sha256(args.output), "unit_count": len(rows)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
