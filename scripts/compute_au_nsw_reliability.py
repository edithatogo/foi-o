"""Compute descriptive reliability for the locked AU-NSW annotation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_reliability import compute_descriptive

REPORT_SHA = "74125814a8d3da0d161db777e8884847fa5c2bbe1c4f634e8aab228125ee6455"


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
            expected_unit_count=100,
            annotation_prefix="au-nsw",
            schema="foi-o.au-nsw-descriptive-reliability.v1",
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
