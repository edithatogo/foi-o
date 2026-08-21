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
LEGACY_REPLAY_SCHEMA = "fyi-archive.au-rtk-replay-result.v1"
NORMALIZED_REPLAY_SHA256 = "3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807"


def _sha256(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
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
    if _sha256(path.read_bytes()) != metadata["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch")


def _bounded_file(root: Path, name: object, label: str) -> Path:
    candidate = Path(str(name or ""))
    if candidate.name != str(name) or candidate.is_absolute():
        raise ValueError(f"{label} path is not a simple filename")
    path = root / candidate
    if path.is_symlink() or path.resolve(strict=False).parent != root.resolve():
        raise ValueError(f"{label} path escaped its approved root")
    return path


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


def validate_legacy_replay_summary(summary_path: Path) -> dict[str, Any]:
    """Validate the legacy replay envelope without treating it as classification."""
    value = json.loads(summary_path.read_text(encoding="utf-8"))
    if value.get("schema") != LEGACY_REPLAY_SCHEMA:
        raise ValueError("legacy replay summary schema is not recognized")
    if value.get("status") != "candidate_non_final":
        raise ValueError("legacy replay summary is not a non-final candidate")
    if (
        value.get("selection_sha256")
        != "a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51"
    ):
        raise ValueError("legacy replay summary selection pin mismatch")
    if value.get("record_count") != 2082 or value.get("captured_count") != 2082:
        raise ValueError("legacy replay summary does not cover the approved population")
    if value.get("failed_count") != 0 or value.get("pending_count") != 0:
        raise ValueError("legacy replay summary contains failed or pending records")
    if value.get("circuit_open") is not False:
        raise ValueError("legacy replay summary circuit state is not closed")
    if value.get("publication") is not False or value.get("redistribution") is not False:
        raise ValueError("legacy replay summary has an external-action flag")
    if value.get("manifest_finalization_authorized") is not False:
        raise ValueError("legacy replay summary authorizes manifest finalization")
    if value.get("normalized_candidate_sha256") != NORMALIZED_REPLAY_SHA256:
        raise ValueError("legacy replay summary normalized-candidate pin mismatch")
    return {
        "ok": True,
        "schema": LEGACY_REPLAY_SCHEMA,
        "selection_sha256": value["selection_sha256"],
        "record_count": value["record_count"],
        "normalized_candidate_sha256": value["normalized_candidate_sha256"],
        "classification_validation_required": True,
    }


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
    index_path = _bounded_file(candidate_root, index_metadata["path"], "replay index")
    _artifact(index_path, index_metadata, "replay index")
    index_records = _jsonl(index_path)
    index = {record.get("canonical_slug"): record for record in index_records}
    if len(index) != len(index_records) or None in index:
        raise ValueError("replay index contains missing or duplicate canonical slugs")
    if len(index) != summary["captured_record_count"]:
        raise ValueError("replay index does not cover the approved population")

    for slug, entry in index.items():
        raw_path = _bounded_file(
            replay_root / "raw",
            entry["raw_filename"],
            f"raw replay {slug}",
        )
        record_path = _bounded_file(
            replay_root / "records",
            entry["record_filename"],
            f"parsed replay {slug}",
        )
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
        path = _bounded_file(candidate_root, metadata["path"], f"{jurisdiction} output")
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
        "summary_sha256": _sha256(summary_path.read_bytes()),
        "manifest_finalization_authorized": False,
    }
