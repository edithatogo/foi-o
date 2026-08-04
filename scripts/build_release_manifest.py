#!/usr/bin/env python3
"""Build or validate the FOI-O public-safe release manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.release_manifest import build_release_manifest, validate_release_manifest

INCLUDE_FILES = (
    "CITATION.cff",
    "LICENSE-CODE.md",
    "LICENSE-CONTENT.md",
    "LICENSE.md",
    "contexts/foi-o-nz.context.jsonld",
    "ontology/foi-o-nz.ttl",
    "shacl/foi-o-nz.shapes.ttl",
    "vocab/agent-boundaries.skos.ttl",
    "vocab/assertion-status.skos.ttl",
    "vocab/event-types.skos.ttl",
    "vocab/request-states.skos.ttl",
)
INCLUDE_ROOTS = ()
LICENSE_POLICY = {
    "CITATION.cff": "CC-BY-4.0",
    "LICENSE-CODE.md": "MIT",
    "LICENSE-CONTENT.md": "CC-BY-4.0",
    "LICENSE.md": "CC-BY-4.0",
    "contexts": "MIT",
    "ontology": "CC-BY-4.0",
    "shacl": "MIT",
    "vocab": "CC-BY-4.0",
}
EXCLUDED_CLASSES = (
    "authentic_source_content",
    "archive_payloads",
    "attachments",
    "restricted_evidence",
    "credentials",
    "unapproved_empirical_records",
    "training_data",
    "legal_conclusions",
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--repo", type=Path, default=Path.cwd())
    result.add_argument("--revision")
    result.add_argument("--output", type=Path)
    result.add_argument("--validate", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    if bool(args.validate) == bool(args.revision and args.output):
        raise SystemExit("choose either --validate or both --revision and --output")
    if args.validate:
        manifest = json.loads(args.validate.read_text(encoding="utf-8"))
        errors = validate_release_manifest(manifest, repo=args.repo)
        if errors:
            print("\n".join(errors))
            return 1
        print("release manifest validation: PASS")
        return 0
    manifest = build_release_manifest(
        repo=args.repo,
        revision=args.revision,
        include_files=INCLUDE_FILES,
        include_roots=INCLUDE_ROOTS,
        excluded_classes=EXCLUDED_CLASSES,
        license_policy=LICENSE_POLICY,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest["manifest_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
