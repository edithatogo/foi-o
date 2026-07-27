"""Finalize one approved restricted-local AU RightToKnow immutable manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_immutable_manifest import write_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay-selection", type=Path, required=True)
    parser.add_argument("--normalized-replay", type=Path, required=True)
    parser.add_argument("--classification-summary", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--completion-candidate", type=Path, required=True)
    parser.add_argument("--completion-selection", type=Path, required=True)
    parser.add_argument("--query-plan", type=Path, required=True)
    parser.add_argument("--response-bodies-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        arguments = vars(args).copy()
        output = arguments.pop("output")
        result = write_manifest(output, **arguments)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
