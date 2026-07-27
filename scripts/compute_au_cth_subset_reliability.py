"""Compute descriptive reliability for the locked AU-CTH annotation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_reliability import compute_descriptive

REPORT_SHA = "22f5850badf02b0730f30fb1221bcc9fa7f6e74ac46338755a6e777eaff1db32"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compute_descriptive(
            report_path=args.report,
            output_path=args.output,
            expected_report_sha=REPORT_SHA,
            expected_unit_count=385,
            annotation_prefix="au-cth",
            schema="foi-o.au-cth-subset-descriptive-reliability.v1",
            include_gold_and_profile_boundaries=False,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
