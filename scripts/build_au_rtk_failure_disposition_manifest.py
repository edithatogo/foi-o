"""Finalize an approved AU RightToKnow manifest with nine explicit 404 exclusions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_immutable_manifest import (
    write_failure_disposition_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay-selection", type=Path, required=True)
    parser.add_argument("--failure-ledger", type=Path, required=True)
    parser.add_argument("--replay-index", type=Path, required=True)
    parser.add_argument("--classification-summary", type=Path, required=True)
    parser.add_argument("--approved-failure-ledger-sha256", required=True)
    parser.add_argument("--authorization-confirmation", required=True)
    args = parser.parse_args()
    try:
        arguments = vars(args).copy()
        output = arguments.pop("output")
        result = write_failure_disposition_manifest(output, **arguments)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
