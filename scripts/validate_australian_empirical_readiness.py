"""Validate and report Australian empirical-input readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_empirical_readiness import (
    AustralianEmpiricalReadiness,
    audit_australian_empirical_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT
    / "conductor"
    / "tracks"
    / "australian_jurisdiction_profiles_20260714"
    / "phase-3-readiness.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = audit_australian_empirical_readiness(
        AustralianEmpiricalReadiness.model_validate(payload)
    )
    print(result.model_dump_json(indent=2))
    return 2 if args.require_ready and not result.ready else 0


if __name__ == "__main__":
    raise SystemExit(main())
