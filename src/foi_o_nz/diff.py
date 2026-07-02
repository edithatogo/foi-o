"""JSONL stream diff utilities for incremental FOI-O NZ artefacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from foi_o_nz.io import iter_jsonl, write_json
from foi_o_nz.ledger import canonical_record_json, infer_record_id, sha256_text

DIFF_SCHEMA_VERSION = "foi-o-nz.diff.v0.1.0"


class DiffItem(BaseModel):
    """One changed record in a JSONL stream diff."""

    model_config = ConfigDict(extra="forbid")

    record_id: str
    status: Literal["added", "removed", "modified", "unchanged"]
    before_sha256: str | None = None
    after_sha256: str | None = None


class DiffReport(BaseModel):
    """Summary of two JSONL streams compared by stable record ID."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.diff.v0.1.0"] = DIFF_SCHEMA_VERSION
    ok: bool = True
    before: str
    after: str
    key: str | None = None
    counts: dict[str, int]
    changes: list[DiffItem]


def _index_records(path: Path, *, key: str | None = None) -> dict[str, tuple[str, dict[str, Any]]]:
    indexed: dict[str, tuple[str, dict[str, Any]]] = {}
    for sequence, record in enumerate(iter_jsonl(path)):
        record_id = (
            str(record.get(key))
            if key is not None and record.get(key) is not None
            else infer_record_id(record, sequence)
        )
        record_hash = sha256_text(canonical_record_json(record))
        indexed[record_id] = (record_hash, record)
    return indexed


def diff_jsonl_records(
    before_path: Path, after_path: Path, *, key: str | None = None
) -> DiffReport:
    """Compare two JSONL files and return a deterministic diff report."""
    before = _index_records(before_path, key=key)
    after = _index_records(after_path, key=key)
    all_ids = sorted(set(before) | set(after))
    changes: list[DiffItem] = []
    counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    for record_id in all_ids:
        before_hash = before.get(record_id, (None,))[0]
        after_hash = after.get(record_id, (None,))[0]
        if before_hash is None:
            status = "added"
        elif after_hash is None:
            status = "removed"
        elif before_hash == after_hash:
            status = "unchanged"
        else:
            status = "modified"
        counts[status] += 1
        if status != "unchanged":
            changes.append(
                DiffItem(
                    record_id=record_id,
                    status=status,  # type: ignore[arg-type]
                    before_sha256=before_hash,
                    after_sha256=after_hash,
                )
            )
    return DiffReport(
        before=str(before_path),
        after=str(after_path),
        key=key,
        counts=counts,
        changes=changes,
    )


def diff_jsonl(
    before_path: Path, after_path: Path, output_json: Path, *, key: str | None = None
) -> dict[str, Any]:
    """Write a JSONL diff report."""
    report = diff_jsonl_records(before_path, after_path, key=key).model_dump(
        mode="json", exclude_none=True
    )
    write_json(output_json, report)
    return report
