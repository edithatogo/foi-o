#!/usr/bin/env python3
"""Intentionally raise the coverage baseline in .coverage-baseline.json.

Run only as a reviewed, intentional change (``make coverage-ratchet-update``):
the baseline may move up, never down.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".coverage-baseline.json"


def main() -> int:
    coverage_path = ROOT / "coverage.json"
    if not coverage_path.exists():
        print("coverage.json not found; run pytest with --cov first")
        return 1
    total = json.loads(coverage_path.read_text())["totals"]["percent_covered"]
    current = json.loads(BASELINE.read_text())["baseline_percent"] if BASELINE.exists() else 0.0
    if total < current:
        print(f"refusing to lower baseline: current {current:.2f}% > measured {total:.2f}%")
        return 1
    BASELINE.write_text(json.dumps({"baseline_percent": round(total, 2)}, indent=2) + "\n")
    print(f"baseline raised: {current:.2f}% -> {total:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
