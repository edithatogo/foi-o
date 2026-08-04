#!/usr/bin/env python3
"""Build or validate a deterministic destination-neutral release archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from foi_o_nz.release_manifest import build_release_bundle, validate_release_bundle

ROOT = Path(__file__).parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--repo", type=Path, default=Path.cwd())
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--bundle", type=Path, required=True)
    result.add_argument("--receipt", type=Path, required=True)
    result.add_argument("--bundle-name")
    result.add_argument("--validate", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.validate:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        schema = json.loads(
            (ROOT / "schemas/json/release-bundle-receipt.schema.json").read_text(encoding="utf-8")
        )
        schema_errors = [
            f"release bundle receipt schema: {error.message}"
            for error in Draft202012Validator(schema).iter_errors(receipt)
        ]
        errors = validate_release_bundle(
            receipt, bundle=args.bundle, manifest=manifest, repo=args.repo
        )
        errors = [*schema_errors, *errors]
        if errors:
            print("\n".join(errors))
            return 1
        print("release bundle validation: PASS")
        return 0
    if not args.bundle_name:
        raise SystemExit("--bundle-name is required when building")
    receipt = build_release_bundle(
        manifest=manifest,
        repo=args.repo,
        output=args.bundle,
        bundle_name=args.bundle_name,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(receipt["bundle_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
