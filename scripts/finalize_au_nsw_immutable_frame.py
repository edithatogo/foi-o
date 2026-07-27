"""Finalize and validate the approved restricted-local AU-NSW frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_nsw_candidate_frame import build_immutable_frame, validate_immutable_frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_immutable_frame(args.output)
            if args.validate_only
            else build_immutable_frame(args.candidate, args.output)
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"units", "duplicate_registry"}
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
