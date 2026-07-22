"""Validate a non-frozen AU-CTH candidate ledger before rights review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def validate_ledger(
    ledger: dict[str, Any], *, calibration_urls: set[str], expected_cdx_sha256: str
) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema") != "foi-o.au-cth-fresh-candidate-ledger.v0.1.0":
        errors.append("unsupported ledger schema")
    if ledger.get("calibration_excluded") is not True:
        errors.append("calibration exclusion is not asserted")
    if ledger.get("source_cdx_sha256") != expected_cdx_sha256:
        errors.append("source CDX hash does not match expected export")
    records = ledger.get("records")
    if not isinstance(records, list) or not records:
        errors.append("candidate records are missing")
        return errors
    urls: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        url = record.get("source_url")
        if not isinstance(url, str) or not url:
            errors.append(f"record {index} lacks source_url")
            continue
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "www.righttoknow.org.au"
            or not parsed.path.startswith("/request/")
        ):
            errors.append(f"record {index} is outside AU RightToKnow request scope")
        if "?" in url or "#" in url:
            errors.append(f"record {index} is not canonicalized")
        if url in calibration_urls:
            errors.append(f"record {index} is a calibration URL")
        if not isinstance(record.get("archive_timestamp"), str) or not record["archive_timestamp"]:
            errors.append(f"record {index} lacks archive_timestamp")
        if not isinstance(record.get("archive_digest"), str) or not record["archive_digest"]:
            errors.append(f"record {index} lacks archive_digest")
        urls.append(url)
    if len(urls) != len(set(urls)):
        errors.append("candidate URLs are not unique")
    if urls != sorted(urls):
        errors.append("candidate URLs are not in deterministic lexical order")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--calibration-url", action="append", default=[])
    parser.add_argument("--cdx-sha256", required=True)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"ERROR: ledger is not readable JSON: {error}")
        return 1
    errors = validate_ledger(
        ledger, calibration_urls=set(args.calibration_url), expected_cdx_sha256=args.cdx_sha256
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("AU fresh candidate ledger: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
