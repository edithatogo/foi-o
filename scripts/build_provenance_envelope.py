"""Build one content-addressed provenance envelope from a JSON run specification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.provenance import build_envelope, canonical_bytes


def main() -> int:
    """Build and write a validated envelope."""
    parser = argparse.ArgumentParser()
    parser.add_argument("specification", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.specification.read_text(encoding="utf-8"))
    envelope = build_envelope(
        envelope_id=spec["envelope_id"],
        transformation_contract=spec["transformation_contract"],
        run_occurrence=spec["run_occurrence"],
        authorization=spec["authorization"],
        inputs=spec["inputs"],
        outputs=spec["outputs"],
        population=spec["population"],
        successor_effects=spec.get("successor_effects", []),
        lineage=spec.get("lineage", []),
    )
    args.output.write_bytes(canonical_bytes(envelope) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
