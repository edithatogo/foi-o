"""Build or validate the approved AU-NSW remediation holdout complement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_nsw_sampling import build_fresh_holdout, validate_fresh_holdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--prior-membership", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_fresh_holdout(
                args.output, frame_path=args.frame, prior_membership_path=args.prior_membership
            )
            if args.validate_only
            else build_fresh_holdout(
                frame_path=args.frame,
                prior_membership_path=args.prior_membership,
                output=args.output,
            )
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
