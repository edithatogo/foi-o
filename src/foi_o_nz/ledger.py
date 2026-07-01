"""Tamper-evident JSONL ledger utilities.

The ledger is intentionally simple: every source record is canonicalised, hashed,
and then linked to the previous ledger hash. This does not certify legal content;
it creates an auditable evidence trail that agents can verify before using data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from foi_o_nz.constants import LEDGER_SCHEMA_VERSION
from foi_o_nz.encoding import dumps_json
from foi_o_nz.io import iter_jsonl, write_json, write_jsonl

ZERO_HASH = "0" * 64


class LedgerEntry(BaseModel):
    """One hash-chain entry for a request/event/chunk/embedding record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.ledger.v0.1.0"] = LEDGER_SCHEMA_VERSION
    sequence: int = Field(ge=0)
    record_type: str
    record_id: str
    algorithm: Literal["sha256-json-c14n-v1"] = "sha256-json-c14n-v1"
    previous_hash: str
    record_sha256: str
    ledger_hash: str
    generated_at: datetime

    @field_validator("previous_hash", "record_sha256", "ledger_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        """Validate SHA-256 hex digests."""
        lowered = value.lower()
        if len(lowered) != 64 or any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("hash must be a 64-character lowercase SHA-256 hex digest")
        return lowered


def canonical_record_json(record: dict[str, Any]) -> str:
    """Return deterministic canonical JSON text for hashing."""
    return dumps_json(record, pretty=False, sort_keys=True)


def sha256_text(text: str) -> str:
    """Return SHA-256 hex digest of UTF-8 text."""
    return sha256(text.encode("utf-8")).hexdigest()


def infer_record_id(record: dict[str, Any], sequence: int) -> str:
    """Infer a stable record identifier from known FOI-O NZ record shapes."""
    for key in ("event_id", "chunk_id", "embedding_id", "ledger_hash"):
        value = record.get(key)
        if value is not None:
            return str(value)
    request_id = record.get("request_id")
    if request_id is not None:
        return str(request_id)
    request_ref = record.get("request_ref")
    if isinstance(request_ref, dict):
        source_request_id = request_ref.get("source_request_id")
        if source_request_id is not None:
            return str(source_request_id)
    return f"record-{sequence}"


def build_ledger_entries(
    records: list[dict[str, Any]],
    *,
    record_type: str,
    previous_hash: str = ZERO_HASH,
    generated_at: datetime | None = None,
) -> list[LedgerEntry]:
    """Build a deterministic hash-chain ledger for records."""
    generated_at = generated_at or datetime.now(UTC)
    entries: list[LedgerEntry] = []
    prior = previous_hash
    for sequence, record in enumerate(records):
        canonical = canonical_record_json(record)
        record_hash = sha256_text(canonical)
        chain_material = dumps_json(
            {
                "algorithm": "sha256-json-c14n-v1",
                "previous_hash": prior,
                "record_id": infer_record_id(record, sequence),
                "record_sha256": record_hash,
                "record_type": record_type,
                "sequence": sequence,
            },
            pretty=False,
            sort_keys=True,
        )
        ledger_hash = sha256_text(chain_material)
        entry = LedgerEntry(
            sequence=sequence,
            record_type=record_type,
            record_id=infer_record_id(record, sequence),
            previous_hash=prior,
            record_sha256=record_hash,
            ledger_hash=ledger_hash,
            generated_at=generated_at,
        )
        entries.append(entry)
        prior = ledger_hash
    return entries


def build_ledger_jsonl(
    input_jsonl: Path,
    output_jsonl: Path,
    *,
    record_type: str,
    previous_hash: str = ZERO_HASH,
) -> dict[str, Any]:
    """Create a ledger JSONL file for a source JSONL stream."""
    records = list(iter_jsonl(input_jsonl))
    entries = build_ledger_entries(records, record_type=record_type, previous_hash=previous_hash)
    write_jsonl(output_jsonl, [entry.model_dump(mode="json") for entry in entries])
    result = {
        "ok": True,
        "input": str(input_jsonl),
        "output": str(output_jsonl),
        "record_type": record_type,
        "entry_count": len(entries),
        "root_hash": entries[-1].ledger_hash if entries else previous_hash,
        "previous_hash": previous_hash,
        "algorithm": "sha256-json-c14n-v1",
    }
    write_json(output_jsonl.with_suffix(output_jsonl.suffix + ".manifest.json"), result)
    return result


def verify_ledger_jsonl(
    input_jsonl: Path,
    ledger_jsonl: Path,
    *,
    record_type: str,
    previous_hash: str = ZERO_HASH,
) -> dict[str, Any]:
    """Verify a ledger against its source JSONL stream."""
    records = list(iter_jsonl(input_jsonl))
    expected = [
        entry.model_dump(mode="json")
        for entry in build_ledger_entries(records, record_type=record_type, previous_hash=previous_hash)
    ]
    observed = list(iter_jsonl(ledger_jsonl))
    errors: list[str] = []
    if len(expected) != len(observed):
        errors.append(f"entry count mismatch: expected {len(expected)}, observed {len(observed)}")
    for idx, (want, got) in enumerate(zip(expected, observed, strict=False)):
        for key in ("sequence", "record_type", "record_id", "previous_hash", "record_sha256", "ledger_hash"):
            if want.get(key) != got.get(key):
                errors.append(f"entry {idx} {key} mismatch: expected {want.get(key)!r}, observed {got.get(key)!r}")
                break
    return {
        "ok": not errors,
        "input": str(input_jsonl),
        "ledger": str(ledger_jsonl),
        "record_type": record_type,
        "entry_count": len(observed),
        "root_hash": observed[-1]["ledger_hash"] if observed else previous_hash,
        "errors": errors,
    }
