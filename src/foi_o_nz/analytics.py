"""Optional analytics helpers backed by Polars and DuckDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import iter_jsonl, write_json


def summarise_requests_jsonl(path: Path) -> dict[str, Any]:
    """Summarise request profile JSONL without mandatory dataframe dependencies."""
    count = 0
    by_state: dict[str, int] = {}
    by_authority: dict[str, int] = {}
    for record in iter_jsonl(path):
        count += 1
        state = str(record.get("normalised_state") or "Unknown")
        authority = str(record.get("authority") or "Unknown authority")
        by_state[state] = by_state.get(state, 0) + 1
        by_authority[authority] = by_authority.get(authority, 0) + 1
    return {
        "record_count": count,
        "normalised_state_counts": dict(sorted(by_state.items())),
        "top_authorities": dict(sorted(by_authority.items(), key=lambda item: item[1], reverse=True)[:20]),
    }


def write_summary(path: Path, output: Path) -> dict[str, Any]:
    """Write a JSON summary for request JSONL."""
    summary = summarise_requests_jsonl(path)
    write_json(output, summary)
    return summary


def duckdb_summary(parquet_path: Path) -> list[dict[str, Any]]:
    """Summarise Parquet requests with DuckDB if installed."""
    try:
        import duckdb  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("duckdb is required for duckdb_summary") from exc
    query = """
        SELECT normalised_state, count(*) AS n
        FROM read_parquet(?)
        GROUP BY normalised_state
        ORDER BY n DESC, normalised_state
    """
    return duckdb.connect().execute(query, [str(parquet_path)]).fetchdf().to_dict("records")
