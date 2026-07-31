#!/usr/bin/env python3
"""Classify JSONL authority evidence through a pinned Australian registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from foi_o_nz.australian_authorities import classify_authority, validate_registry


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()

    registry = _load_json(args.registry)
    validate_registry(registry)
    results: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        args.input.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        evidence = json.loads(line)
        if not isinstance(evidence, dict):
            raise ValueError(f"input line {line_number} must be a JSON object")
        results.append(classify_authority(evidence, registry, as_of=args.as_of))

    payload = "".join(
        json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n" for result in results
    )
    args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
