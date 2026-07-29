"""Validate one restricted-local AU RightToKnow immutable manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_immutable_manifest import validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = validate_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
