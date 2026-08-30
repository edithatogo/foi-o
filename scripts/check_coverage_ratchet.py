#!/usr/bin/env python3
"""Coverage ratchet: fail when total coverage drops below the recorded baseline.

Unlike a fixed ``fail_under`` cliff, the baseline is monotonic: it can only be
raised intentionally (``make coverage-ratchet-update``), so robustness improves
without regressing. Reads ``coverage.json`` produced by ``pytest --cov``.
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
        print("COVERAGE-RATCHET-FAIL: coverage.json not found; run pytest with --cov")
        return 1
    data = json.loads(coverage_path.read_text())
    total = data.get("totals", {}).get("percent_covered")
    if total is None:
        print("COVERAGE-RATCHET-FAIL: coverage.json missing totals.percent_covered")
        return 1
    baseline = 0.0
    if BASELINE.exists():
        baseline = json.loads(BASELINE.read_text())["baseline_percent"]
    if total + 1e-9 < baseline:
        print(f"COVERAGE-RATCHET-FAIL: total {total:.2f}% below baseline {baseline:.2f}%")
        return 1
    print(f"COVERAGE-RATCHET-OK: total {total:.2f}% >= baseline {baseline:.2f}%")
    if total > baseline + 0.05:
        print(
            "COVERAGE-RATCHET-NOTE: baseline can be raised via "
            "`make coverage-ratchet-update` (intentional, reviewed change)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
