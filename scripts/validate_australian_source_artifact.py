"""Validate an authentic Australian source artifact before empirical use."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

JURISDICTION_REGIME = {"AU-CTH": "FOI", "AU-NSW": "GIPA"}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_artifact(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    try:
        artifact: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"artifact is not readable JSON: {error}"]

    if artifact.get("schema_version") != "foi-o.australian-source-artifact.v0.1.0":
        errors.append("unsupported schema_version")
    if artifact.get("status") != "authentic_frozen_candidate":
        errors.append("artifact is not an authentic frozen candidate")
    jurisdiction = artifact.get("jurisdiction")
    if jurisdiction not in JURISDICTION_REGIME:
        errors.append("jurisdiction must be AU-CTH or AU-NSW")
    elif artifact.get("regime") != JURISDICTION_REGIME[jurisdiction]:
        errors.append("regime does not match jurisdiction")
    if artifact.get("rights_review_status") != "approved":
        errors.append("rights review is not approved")

    records_path = root / str(artifact.get("records_path", ""))
    if not records_path.is_file():
        errors.append("records_path does not identify a file")
        return errors
    actual_bytes = records_path.stat().st_size
    actual_digest = _digest(records_path)
    if artifact.get("byte_count") != actual_bytes:
        errors.append("byte_count does not match records file")
    if artifact.get("records_sha256") != actual_digest:
        errors.append("records_sha256 does not match records file")

    actual_count = 0
    try:
        for line_number, line in enumerate(records_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            actual_count += 1
            if record.get("jurisdiction") != jurisdiction:
                errors.append(f"record {line_number} has the wrong jurisdiction")
            if "candidate_label" in record or "extractor_output" in record:
                errors.append(f"record {line_number} contains extractor/candidate output")
            if not isinstance(record.get("source_url"), str) or not record["source_url"]:
                errors.append(f"record {line_number} lacks source_url")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"records file is not valid UTF-8 JSONL: {error}")
    if artifact.get("record_count") != actual_count:
        errors.append("record_count does not match records file")
    if actual_count == 0:
        errors.append("records file is empty")
    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate_artifact(args.artifact, args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Australian source artifact: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
