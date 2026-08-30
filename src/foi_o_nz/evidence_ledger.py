"""Canonical evidence ledger successor validation and append utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Compute the SHA-256 digest of a file's byte contents."""
    return _sha256(path.read_bytes())


def validate_successor_evidence_ledger(
    successor_path: Path,
    legacy_path: Path,
    expected_legacy_sha256: str,
) -> dict[str, Any]:
    """Validate a canonical successor evidence ledger against its predecessor pin."""
    if not legacy_path.exists():
        raise ValueError(f"legacy evidence ledger does not exist: {legacy_path}")
    actual_legacy_sha256 = compute_file_sha256(legacy_path)
    if actual_legacy_sha256 != expected_legacy_sha256:
        raise ValueError(
            f"legacy evidence ledger SHA-256 mismatch: expected {expected_legacy_sha256}, got {actual_legacy_sha256}"
        )

    if not successor_path.exists():
        return {
            "status": "ready_for_initialization",
            "legacy_sha256": actual_legacy_sha256,
            "entry_count": 0,
        }

    lines = [
        line.strip()
        for line in successor_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not lines:
        return {
            "status": "empty_successor",
            "legacy_sha256": actual_legacy_sha256,
            "entry_count": 0,
        }

    prev_hash = actual_legacy_sha256
    entries: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as err:
            raise ValueError(f"invalid JSON on line {idx + 1}: {err}") from err

        if not isinstance(entry, dict):
            raise ValueError(f"entry on line {idx + 1} must be an object")

        if entry.get("predecessor_sha256") != prev_hash:
            raise ValueError(
                f"hash chain break on line {idx + 1}: expected predecessor {prev_hash}, got {entry.get('predecessor_sha256')}"
            )

        required_fields = ["event_id", "timestamp", "kind", "predecessor_sha256", "payload"]
        for req in required_fields:
            if req not in entry:
                raise ValueError(f"missing required field '{req}' on line {idx + 1}")

        # Compute content hash of this entry
        canonical_bytes = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
        prev_hash = _sha256(canonical_bytes)
        entries.append(entry)

    return {
        "status": "valid_successor_chain",
        "legacy_sha256": actual_legacy_sha256,
        "entry_count": len(entries),
        "tip_sha256": prev_hash,
    }


def append_successor_evidence_event(
    successor_path: Path,
    legacy_path: Path,
    expected_legacy_sha256: str,
    event: dict[str, Any],
) -> str:
    """Safely append an event to the successor ledger, preserving predecessor pins."""
    chain_info = validate_successor_evidence_ledger(
        successor_path, legacy_path, expected_legacy_sha256
    )
    predecessor_hash = chain_info.get("tip_sha256") or chain_info["legacy_sha256"]

    event_record = {
        "event_id": event.get("event_id")
        or f"ev-{hashlib.sha256(json.dumps(event).encode()).hexdigest()[:12]}",
        "timestamp": event.get("timestamp") or "2026-08-30T17:15:00Z",
        "kind": event.get("kind", "evidence_checkpoint"),
        "predecessor_sha256": predecessor_hash,
        "payload": event.get("payload", {}),
    }

    line = json.dumps(event_record, sort_keys=True) + "\n"
    with successor_path.open("a", encoding="utf-8") as f:
        f.write(line)

    return _sha256(json.dumps(event_record, sort_keys=True, separators=(",", ":")).encode("utf-8"))
