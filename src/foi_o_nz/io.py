"""I/O helpers for JSON and JSONL records."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


def read_json_records(path: Path) -> list[dict[str, Any]]:
    """Read JSONL or JSON-array records from ``path``."""
    if path.suffix.lower() == ".jsonl":
        return list(iter_jsonl(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [record for record in data if isinstance(record, dict)]
    if isinstance(data, dict):
        records = data.get("records")
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
        return [data]
    raise ValueError(f"Unsupported JSON structure in {path}")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON records from a JSONL file."""
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            if not isinstance(data, dict):
                raise ValueError(f"Expected object on line {line_no} of {path}")
            yield data


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Write records to JSONL and return the count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str))
            handle.write("\n")
            count += 1
    return count


def write_json(path: Path, data: Any) -> None:
    """Write pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
