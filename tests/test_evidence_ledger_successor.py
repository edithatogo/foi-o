from __future__ import annotations

import json
from pathlib import Path

import pytest

from foi_o_nz.evidence_ledger import (
    append_successor_evidence_event,
    compute_file_sha256,
    validate_successor_evidence_ledger,
)


def test_validate_empty_successor(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text('{"event": 1}\n{"event": 2}\n', encoding="utf-8")
    legacy_sha = compute_file_sha256(legacy)
    successor = tmp_path / "successor.jsonl"

    res = validate_successor_evidence_ledger(successor, legacy, legacy_sha)
    assert res["status"] == "ready_for_initialization"
    assert res["entry_count"] == 0


def test_append_and_validate_successor_chain(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text('{"event": 1}\n{"event": 2}\n', encoding="utf-8")
    legacy_sha = compute_file_sha256(legacy)
    successor = tmp_path / "successor.jsonl"

    event1 = {"event_id": "ev-001", "kind": "test_checkpoint", "payload": {"k": "v1"}}
    append_successor_evidence_event(successor, legacy, legacy_sha, event1)

    event2 = {"event_id": "ev-002", "kind": "test_checkpoint", "payload": {"k": "v2"}}
    h2 = append_successor_evidence_event(successor, legacy, legacy_sha, event2)

    res = validate_successor_evidence_ledger(successor, legacy, legacy_sha)
    assert res["status"] == "valid_successor_chain"
    assert res["entry_count"] == 2
    assert res["tip_sha256"] == h2


def test_reject_mismatched_legacy_hash(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text('{"event": 1}\n', encoding="utf-8")
    successor = tmp_path / "successor.jsonl"

    with pytest.raises(ValueError, match="legacy evidence ledger SHA-256 mismatch"):
        validate_successor_evidence_ledger(successor, legacy, "0" * 64)


def test_reject_broken_hash_chain(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text('{"event": 1}\n', encoding="utf-8")
    legacy_sha = compute_file_sha256(legacy)
    successor = tmp_path / "successor.jsonl"

    # Write entry with wrong predecessor hash
    entry = {
        "event_id": "ev-001",
        "timestamp": "2026-08-30T17:15:00Z",
        "kind": "test",
        "predecessor_sha256": "f" * 64,
        "payload": {},
    }
    successor.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="hash chain break"):
        validate_successor_evidence_ledger(successor, legacy, legacy_sha)
