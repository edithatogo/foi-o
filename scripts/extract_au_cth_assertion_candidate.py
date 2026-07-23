"""Candidate-only AU-CTH assertion extractor with explicit evidence spans."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CODEBOOK_ID = "foio-au-pilot-assertion-v0.2.0"
PATTERNS = (
    re.compile(r"\b(?:a\s+)?Freedom of Information request to\b.{0,300}", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:request under|under)\s+the\s+Freedom of Information Act\b", re.IGNORECASE),
    re.compile(r"\bCommonwealth\b.{0,120}\b(?:Freedom of Information|FOI)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:Freedom of Information|FOI)\b.{0,120}\bCommonwealth\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:Australian Government|federal government)\b.{0,120}\b(?:Freedom of Information|FOI)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:Freedom of Information|FOI)\b.{0,120}\b(?:Australian Government|federal government)\b", re.IGNORECASE | re.DOTALL),
)


def extract_unit(unit: dict[str, Any], *, extractor_revision: str) -> dict[str, Any]:
    text = str(unit.get("text") or "")
    match = next((pattern.search(text) for pattern in PATTERNS if pattern.search(text)), None)
    if match is None:
        return {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "label": "unknown",
            "abstention": True,
            "abstention_reason": "insufficient_evidence",
            "span": None,
            "extractor_revision": extractor_revision,
            "codebook_id": CODEBOOK_ID,
        }
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
        "label": "observed",
        "abstention": False,
        "abstention_reason": None,
        "span": {
            "start": match.start(),
            "end": match.end(),
            "coordinate_system": "utf8_character_half_open",
        },
        "extractor_revision": extractor_revision,
        "codebook_id": CODEBOOK_ID,
    }


def extract(frame_path: Path, *, extractor_revision: str) -> dict[str, Any]:
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    units = [extract_unit(unit, extractor_revision=extractor_revision) for unit in frame["units"]]
    return {
        "schema_version": "foi-o.au-cth-assertion-extractor-output.v0.1.0",
        "status": "candidate_not_promoted",
        "jurisdiction": "AU-CTH",
        "extractor_revision": extractor_revision,
        "codebook_id": CODEBOOK_ID,
        "source_population_sha256": frame["source_population_sha256"],
        "units": units,
        "promotion_allowed": False,
        "publication": False,
        "redistribution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="local-candidate-v0.1.0")
    args = parser.parse_args()
    result = extract(args.frame, extractor_revision=args.revision)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"units": len(result["units"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
