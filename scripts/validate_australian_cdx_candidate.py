"""Validate a bounded Australian CDX artifact and its non-final candidate packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

HEADER = ["original", "timestamp", "digest", "statuscode", "length"]
EXPECTED_SCOPE_HOST = "www.righttoknow.org.au"
EXPECTED_SCOPE_PREFIX = "/request/"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_candidate(
    packet_path: Path,
    schema_path: Path,
    artifact_zip: Path,
    unpacked_root: Path,
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    packet = _load(packet_path)
    schema = _load(schema_path)
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(packet):
        errors.append(f"packet schema: {error.message}")

    retrieval_path = unpacked_root / "retrieval.json"
    cdx_path = unpacked_root / "internet_archive_all_captures_cdx.json"
    pages_root = unpacked_root / "internet_archive_all_captures_cdx.pages"
    checkpoint_path = pages_root / "checkpoint.json"
    required = [artifact_zip, retrieval_path, cdx_path, checkpoint_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return errors + [f"missing required file: {path}" for path in missing], {}

    integrity = packet.get("integrity", {})
    actual_hashes = {
        "artifact_sha256": _sha256(artifact_zip),
        "cdx_sha256": _sha256(cdx_path),
        "retrieval_evidence_sha256": _sha256(retrieval_path),
    }
    for field, actual in actual_hashes.items():
        if integrity.get(field) != actual:
            errors.append(f"{field} mismatch")

    retrieval = _load(retrieval_path)
    checkpoint = _load(checkpoint_path)
    rows = _load(cdx_path)
    if not isinstance(rows, list) or not rows or rows[0] != HEADER:
        return [*errors, "CDX header does not match the approved export contract"], {}

    records = rows[1:]
    page_paths = sorted(pages_root.glob("page-*.json"))
    page_records = 0
    for expected_index, page_path in enumerate(page_paths):
        if page_path.name != f"page-{expected_index:06d}.json":
            errors.append("CDX page sequence is not contiguous")
            break
        page = _load(page_path)
        if (
            not isinstance(page, dict)
            or page.get("page") != expected_index
            or page.get("header") != HEADER
            or not isinstance(page.get("rows"), list)
        ):
            errors.append(f"{page_path.name} has an invalid header")
            continue
        page_records += len(page["rows"])

    valid_records: list[list[str]] = []
    scope_conforming = 0
    for row_number, row in enumerate(records, 2):
        if (
            not isinstance(row, list)
            or len(row) != len(HEADER)
            or not all(isinstance(value, str) for value in row)
        ):
            errors.append(f"CDX row {row_number} is malformed")
            continue
        valid_row = cast("list[str]", row)
        valid_records.append(valid_row)
        parsed = urlsplit(valid_row[0])
        if (
            parsed.scheme in {"http", "https"}
            and (parsed.hostname or "").lower() == EXPECTED_SCOPE_HOST
            and parsed.path.startswith(EXPECTED_SCOPE_PREFIX)
        ):
            scope_conforming += 1

    record_count = len(records)
    capture_keys = Counter((row[0], row[1], row[2]) for row in valid_records)
    stats = {
        "page_count": len(page_paths),
        "record_count": record_count,
        "unique_original_urls": len({row[0] for row in valid_records}),
        "unique_capture_keys": len(capture_keys),
        "duplicate_capture_rows": sum(count - 1 for count in capture_keys.values()),
        "scope_conforming_records": scope_conforming,
    }

    expected_count = retrieval.get("record_count")
    if retrieval.get("pagination_complete") is not True:
        errors.append("retrieval pagination is not complete")
    if retrieval.get("retrieval_status") != "complete":
        errors.append("retrieval status is not complete")
    if retrieval.get("eligible_for_empirical_freeze") is not False:
        errors.append("retrieval must remain ineligible for empirical freeze")
    if retrieval.get("publication") is not False or retrieval.get("redistribution") is not False:
        errors.append("retrieval rights boundary is not fail-closed")
    if retrieval.get("response_sha256") != actual_hashes["cdx_sha256"]:
        errors.append("retrieval response_sha256 does not match CDX")
    if record_count != expected_count or page_records != record_count:
        errors.append("consolidated, paged, and declared record counts differ")
    if checkpoint.get("record_count") != record_count:
        errors.append("checkpoint record count differs")
    if len(page_paths) != retrieval.get("checkpoint", {}).get("page_count"):
        errors.append("page count differs from retrieval evidence")
    if scope_conforming != record_count:
        errors.append("one or more CDX records fall outside the approved URL scope")

    coverage = packet.get("coverage", {})
    for field, actual in stats.items():
        if coverage.get(field) != actual:
            errors.append(f"coverage.{field} mismatch")

    classification = packet.get("metadata_only_classification", {})
    classified_total = sum(
        classification.get(name, -record_count) for name in ("AU-CTH", "AU-NSW", "unresolved")
    )
    if classified_total != record_count:
        errors.append("classification counts do not cover every record")
    # CDX rows contain URL/capture fields only. A URL slug is not authority evidence.
    if classification.get("AU-CTH") != 0 or classification.get("AU-NSW") != 0:
        errors.append("CDX-only records cannot be jurisdiction-resolved without authority metadata")
    if classification.get("unresolved") != record_count:
        errors.append("all CDX-only records must remain unresolved")

    return errors, stats


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--artifact-zip", required=True, type=Path)
    parser.add_argument("--unpacked-root", required=True, type=Path)
    args = parser.parse_args()
    errors, stats = validate_candidate(
        args.packet, args.schema, args.artifact_zip, args.unpacked_root
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Australian CDX candidate: PASS ({json.dumps(stats, sort_keys=True)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
