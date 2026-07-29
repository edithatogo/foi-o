"""Build a provenance-pinned, rights-pending frame from historical full text."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urldefrag, urlsplit, urlunsplit


def _canonical_url(value: str) -> str:
    parts = urlsplit(urldefrag(value)[0])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def build_frame(fulltext_path: Path, *, jurisdiction: str, output: Path) -> dict[str, Any]:
    payload = json.loads(fulltext_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fulltext artifact must be a JSON object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("fulltext artifact contains no records")
    units = []
    for index, raw_record in enumerate(records):
        if not isinstance(raw_record, dict):
            raise ValueError(f"record {index} is not an object")
        record = cast("dict[str, Any]", raw_record)
        source_url = str(record.get("source_url") or "")
        if not source_url:
            raise ValueError(f"record {index} has no source_url")
        text = str(record.get("text") or "")
        status = str(record.get("status") or "unknown")
        digest = record.get("text_sha256") or hashlib.sha256(text.encode()).hexdigest()
        units.append(
            {
                "unit_id": f"{jurisdiction}:historical:{index:06d}",
                "jurisdiction": jurisdiction,
                "text": text if status == "captured" else None,
                "unit_sha256": digest,
                "capture_status": status,
                "source_ref": {
                    "source_url": source_url,
                    "canonical_source_url": _canonical_url(source_url),
                    "archive_timestamp": record.get("archive_timestamp"),
                    "archive_url": record.get("archive_url"),
                    "html_sha256": record.get("html_sha256"),
                    "text_sha256": record.get("text_sha256"),
                    "diagnostic": record.get("diagnostic"),
                },
                "rights_eligible": False,
                "annotation_eligible": False,
            }
        )
    frame = {
        "schema_version": "foi-o.australian-fulltext-frame.v0.1.0",
        "status": "authentic_pending_rights_and_fulltext_review",
        "jurisdiction": jurisdiction,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_fulltext_path": str(fulltext_path),
        "source_fulltext_sha256": hashlib.sha256(fulltext_path.read_bytes()).hexdigest(),
        "source_artifact_schema": payload.get("schema"),
        "record_count": len(units),
        "captured_count": sum(unit["capture_status"] == "captured" for unit in units),
        "failed_count": sum(unit["capture_status"] != "captured" for unit in units),
        "rights_eligible": False,
        "fulltext_available": any(unit["text"] for unit in units),
        "annotation_execution_authorized": False,
        "units": units,
    }
    frame["source_population_sha256"] = hashlib.sha256(
        json.dumps(units, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fulltext", type=Path, required=True)
    parser.add_argument("--jurisdiction", choices=("AU-CTH", "AU-NSW"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_frame(args.fulltext, jurisdiction=args.jurisdiction, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
