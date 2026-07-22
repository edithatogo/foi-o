"""Build a provenance-pinned empirical frame from an authentic archive core export."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_frame(core_path: Path, *, jurisdiction: str, output: Path) -> dict[str, Any]:
    payload = json.loads(core_path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("authentic core contains no records")
    units = []
    for record in records:
        if record.get("extraction_status") != "extracted":
            continue
        source_url = str(record.get("source_url") or "")
        text = " | ".join(
            value for value in (str(record.get("title") or ""), str(record.get("state") or "")) if value
        )
        if not source_url or not text:
            continue
        unit_id = f"{jurisdiction}:{record.get('request_key') or record.get('archive_digest')}"
        units.append({
            "unit_id": unit_id,
            "jurisdiction": jurisdiction,
            "text": text,
            "unit_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "source_ref": {
                "source_url": source_url,
                "archive_url": record.get("archive_url"),
                "archive_digest": record.get("archive_digest"),
                "content_sha256": record.get("content_sha256"),
            },
            "rights_eligible": False,
            "annotation_eligible": False,
        })
    if not units:
        raise ValueError("authentic core has no usable extracted metadata units")
    frame = {
        "schema_version": "foi-o.australian-empirical-frame.v0.1.0",
        "status": "authentic_pending_rights_and_fulltext_review",
        "jurisdiction": jurisdiction,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_core_path": str(core_path),
        "source_core_sha256": hashlib.sha256(core_path.read_bytes()).hexdigest(),
        "source_population_sha256": hashlib.sha256(
            json.dumps(units, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "rights_eligible": False,
        "fulltext_available": False,
        "annotation_execution_authorized": False,
        "units": units,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--jurisdiction", choices=("AU-CTH", "AU-NSW"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_frame(args.core, jurisdiction=args.jurisdiction, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
