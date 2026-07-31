"""Build or validate a bounded Australian jurisdiction rollout contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_rollout_pipeline import validate_contract, write_contract


def _artifact_argument(value: str) -> tuple[str, Path]:
    artifact_id, separator, path = value.partition("=")
    if not separator or not artifact_id or not path:
        raise argparse.ArgumentTypeError("artifact must be ARTIFACT_ID=PATH")
    return artifact_id, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        type=_artifact_argument,
        metavar="ARTIFACT_ID=PATH",
        help="independently verify a declared content pin against a local file",
    )
    args = parser.parse_args()
    try:
        value = json.loads(args.input.read_text(encoding="utf-8"))
        if args.output is None:
            result = validate_contract(value, artifact_files=dict(args.artifact))
        else:
            contract = write_contract(args.output, value)
            result = validate_contract(contract, artifact_files=dict(args.artifact))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
