"""Build or validate the approved AU-NSW restricted-local candidate frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_nsw_candidate_frame import build_candidate_frame, validate_candidate_frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--classification-summary", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_candidate_frame(args.output)
            if args.validate_only
            else build_candidate_frame(
                manifest_path=args.manifest,
                classification_summary=args.classification_summary,
                replay_root=args.replay_root,
                output=args.output,
            )
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    # Candidate frames can contain restricted-local request text. Never emit it
    # to a terminal or CI log merely to report a successful local operation.
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "units"},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
