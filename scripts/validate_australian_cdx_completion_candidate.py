"""Validate an AU RightToKnow canonical CDX completion packet independently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_cdx_completion_candidate import (
    validate_completion_candidate,
)


def main() -> int:
    """Run the fail-closed local completion-packet validator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--query-plan", type=Path, required=True)
    parser.add_argument("--response-bodies-root", type=Path, required=True)
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--selection-sha256")
    args = parser.parse_args()
    try:
        result = validate_completion_candidate(
            args.candidate,
            selection_path=args.selection,
            query_plan_path=args.query_plan,
            response_bodies_root=args.response_bodies_root,
            expected_candidate_sha256=args.candidate_sha256,
            expected_selection_sha256=args.selection_sha256,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
