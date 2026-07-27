"""Run the approved bounded AU-NSW annotation roles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_nsw_annotation import run_annotation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run_annotation(
            membership_path=args.membership,
            frame_path=args.frame,
            codebook_path=args.codebook,
            output_root=args.output_root,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
