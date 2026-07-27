"""Independent validation for bounded Australian archive-replay candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/json/australian-replay-classification-candidate.schema.json"
JURISDICTIONS = ("AU-CTH", "AU-NSW", "OUT_OF_SCOPE", "UNRESOLVED")
PROVENANCE_FIELDS = (
    "canonical_slug",
    "media_kind",
    "source_url",
    "archive_timestamp",
    "archive_digest",
    "raw_sha256",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number} is not a JSON object")
        records.append(value)
    return records


def _artifact(path: Path, metadata: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} is missing")
    if path.stat().st_size != metadata["byte_count"]:
        raise ValueError(f"{label} byte count mismatch")
    if _sha256(path) != metadata["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch")


def _source_boundaries(record: dict[str, Any]) -> None:
    source = urlsplit(str(record.get("source_url") or ""))
    archive = urlsplit(str(record.get("archive_url") or ""))
    if (
        source.scheme not in {"http", "https"}
        or (source.hostname or "").lower() != "www.righttoknow.org.au"
        or not source.path.startswith("/request/")
    ):
        raise ValueError("candidate source URL escaped the approved RightToKnow scope")
    if archive.scheme != "https" or (archive.hostname or "").lower() != "web.archive.org":
        raise ValueError("candidate archive URL escaped Internet Archive")


def validate_replay_candidate(
    summary_path: Path,
    *,
    replay_root: Path,
) -> dict[str, Any]:
    """Validate one complete non-final replay candidate against local source bytes."""
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(summary, schema)
    if sum(summary["counts"].values()) != summary["captured_record_count"]:
        raise ValueError("jurisdiction counts do not cover the approved population")

    candidate_root = summary_path.parent
    index_metadata = summary["replay_index"]
    index_path = candidate_root / index_metadata["path"]
    _artifact(index_path, index_metadata, "replay index")
    index_records = _jsonl(index_path)
    index = {record.get("canonical_slug"): record for record in index_records}
    if len(index) != len(index_records) or None in index:
        raise ValueError("replay index contains missing or duplicate canonical slugs")
    if len(index) != summary["captured_record_count"]:
        raise ValueError("replay index does not cover the approved population")

    for slug, entry in index.items():
        raw_path = replay_root / "raw" / str(entry["raw_filename"])
        record_path = replay_root / "records" / str(entry["record_filename"])
        _artifact(
            raw_path,
            {"byte_count": entry["raw_byte_count"], "sha256": entry["raw_sha256"]},
            f"raw replay {slug}",
        )
        _artifact(
            record_path,
            {
                "byte_count": entry["record_byte_count"],
                "sha256": entry["record_sha256"],
            },
            f"parsed replay {slug}",
        )

    seen: set[str] = set()
    for jurisdiction in JURISDICTIONS:
        metadata = summary["jurisdiction_outputs"][jurisdiction]
        path = candidate_root / metadata["path"]
        _artifact(path, metadata, f"{jurisdiction} output")
        records = _jsonl(path)
        if (
            len(records) != metadata["record_count"]
            or len(records) != summary["counts"][jurisdiction]
        ):
            raise ValueError(f"{jurisdiction} count mismatch")
        for record in records:
            slug = str(record.get("canonical_slug") or "")
            if record.get("jurisdiction") != jurisdiction:
                raise ValueError(f"{jurisdiction} output contains the wrong jurisdiction")
            if not slug or slug in seen or slug not in index:
                raise ValueError(
                    "candidate partition has missing, duplicate, or unknown membership"
                )
            if "candidate_label" in record or "extractor_output" in record:
                raise ValueError("candidate contains extractor or candidate-label output")
            if record.get("status") != "captured" or record.get("parser_version") != 3:
                raise ValueError("candidate contains a failed or stale-parser record")
            if any(record.get(field) != index[slug].get(field) for field in PROVENANCE_FIELDS):
                raise ValueError(f"candidate provenance mismatch: {slug}")
            _source_boundaries(record)
            seen.add(slug)
    if seen != set(index):
        raise ValueError("candidate outputs do not exactly partition the replay index")
    return {
        "ok": True,
        "record_count": len(seen),
        "counts": summary["counts"],
        "summary_sha256": _sha256(summary_path),
        "manifest_finalization_authorized": False,
    }
