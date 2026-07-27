"""Validate a bounded AU RightToKnow replay candidate independently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_replay_candidate import validate_replay_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--replay-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_replay_candidate(args.summary, replay_root=args.replay_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
