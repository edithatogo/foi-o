"""Validate a durable, hash-pinned AU-CTH calibration evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_path(value: Any, root: Path, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} path is missing")
        return None
    path = Path(value)
    if path.is_absolute() or "tmp" in path.parts or "private" in path.parts:
        errors.append(f"{label} path is ephemeral or not relative")
        return None
    resolved = (root / path).resolve()
    if root.resolve() not in resolved.parents and resolved != root.resolve():
        errors.append(f"{label} path escapes manifest root")
        return None
    if not resolved.is_file():
        errors.append(f"{label} path does not identify a file")
        return None
    return resolved


def _check_file(
    entry: dict[str, Any], root: Path, label: str, errors: list[str]
) -> dict[str, Any] | None:
    path = _relative_path(entry.get("path"), root, label, errors)
    digest = entry.get("sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        errors.append(f"{label} has an invalid SHA-256")
    elif path is not None and _digest(path) != digest:
        errors.append(f"{label} SHA-256 does not match file")
    return entry if path is not None else None


def _unit_ids(path: Path, key: str) -> set[str] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    rows = payload.get(key)
    if not isinstance(rows, list):
        return None
    unit_ids: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            unit_id = row.get("unit_id")
            if isinstance(unit_id, str):
                unit_ids.add(unit_id)
    return unit_ids


def validate_manifest(manifest: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != "foi-o.au-cth-calibration-evidence.v0.1.0":
        errors.append("unsupported schema_version")
    if manifest.get("status") != "calibration_only":
        errors.append("calibration status is not explicit")
    if not isinstance(manifest.get("source_population_sha256"), str) or not SHA256.fullmatch(
        manifest["source_population_sha256"]
    ):
        errors.append("source population SHA-256 is missing or invalid")

    codebook = manifest.get("codebook")
    if not isinstance(codebook, dict):
        errors.append("codebook entry is missing")
    else:
        _check_file(codebook, root, "codebook", errors)
        revision = codebook.get("revision")
        if not isinstance(revision, str) or not REVISION.fullmatch(revision):
            errors.append("codebook revision is not a 40-character Git revision")
        elif len(set(revision[7:])) == 1 and revision[7] == "0":
            errors.append("codebook revision is synthetic padded provenance")

    packet_entries = manifest.get("packets")
    annotation_entries = manifest.get("annotations")
    if not isinstance(packet_entries, list) or len(packet_entries) != 2:
        errors.append("exactly two packet entries are required")
        packet_entries = []
    if not isinstance(annotation_entries, list) or len(annotation_entries) != 2:
        errors.append("exactly two annotation entries are required")
        annotation_entries = []

    packet_roles = [entry.get("role") for entry in packet_entries if isinstance(entry, dict)]
    annotation_roles = [
        entry.get("role") for entry in annotation_entries if isinstance(entry, dict)
    ]
    if set(packet_roles) != {"annotator_a", "annotator_b"}:
        errors.append("packet roles must be distinct annotator_a and annotator_b")
    if set(annotation_roles) != {"annotator_a", "annotator_b"}:
        errors.append("annotation roles must be distinct annotator_a and annotator_b")
    for index, entry in enumerate(packet_entries):
        if isinstance(entry, dict):
            _check_file(entry, root, f"packet {index}", errors)
    for index, entry in enumerate(annotation_entries):
        if isinstance(entry, dict):
            _check_file(entry, root, f"annotation {index}", errors)

    adjudication = manifest.get("adjudication")
    if not isinstance(adjudication, dict):
        errors.append("adjudication entry is missing")
    else:
        _check_file(adjudication, root, "adjudication", errors)
        if adjudication.get("role") != "adjudicator":
            errors.append("adjudication role must be distinct adjudicator")

    expected = set(manifest.get("unit_ids") or [])
    if not expected or any(not isinstance(unit_id, str) for unit_id in expected):
        errors.append("unit_ids must be a non-empty set of strings")
    for entry in packet_entries + annotation_entries:
        if not isinstance(entry, dict):
            continue
        path = (root / str(entry.get("path"))).resolve()
        if path.is_file():
            key = (
                "units"
                if entry in packet_entries
                else ("labels" if entry.get("role") == "annotator_a" else "records")
            )
            actual = _unit_ids(path, key)
            if actual is not None and actual != expected:
                errors.append(f"{entry.get('role')} unit membership does not match manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"ERROR: manifest is not readable JSON: {error}")
        return 1
    errors = validate_manifest(manifest, args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("AU calibration evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
