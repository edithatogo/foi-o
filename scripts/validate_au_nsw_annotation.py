"""Validate the bounded AU-NSW annotation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_nsw_annotation import validate_annotation_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        result = validate_annotation_report(args.report)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
