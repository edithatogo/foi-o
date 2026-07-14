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
        "top_authorities": dict(
            sorted(by_authority.items(), key=lambda item: item[1], reverse=True)[:20]
        ),
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


def _confidence_band(value: object) -> str:
    if not isinstance(value, (str, int, float)):
        return "unknown"
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.5:
        return "medium"
    if confidence > 0:
        return "low"
    return "zero"


def summarise_events_jsonl(path: Path) -> dict[str, Any]:
    """Summarise core-event JSONL without mandatory dataframe dependencies."""
    count = 0
    by_type: dict[str, int] = {}
    by_assertion: dict[str, int] = {}
    by_confidence_band: dict[str, int] = {}
    certification_required = 0
    machine_generated = 0
    quality_flags: dict[str, int] = {}
    for record in iter_jsonl(path):
        count += 1
        event_type = str(record.get("event_type") or "Unknown")
        assertion = str(record.get("assertion_status") or "unknown")
        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_assertion[assertion] = by_assertion.get(assertion, 0) + 1
        band = _confidence_band(record.get("confidence"))
        by_confidence_band[band] = by_confidence_band.get(band, 0) + 1
        if record.get("requires_human_certification") is True:
            certification_required += 1
        if record.get("machine_generated") is True:
            machine_generated += 1
        for flag in record.get("quality_flags") or []:
            quality_flags[str(flag)] = quality_flags.get(str(flag), 0) + 1
    return {
        "event_count": count,
        "event_type_counts": dict(sorted(by_type.items())),
        "assertion_status_counts": dict(sorted(by_assertion.items())),
        "confidence_band_counts": dict(sorted(by_confidence_band.items())),
        "requires_human_certification_count": certification_required,
        "machine_generated_count": machine_generated,
        "quality_flag_counts": dict(sorted(quality_flags.items())),
    }


def write_event_summary(path: Path, output: Path) -> dict[str, Any]:
    """Write a JSON summary for event JSONL."""
    summary = summarise_events_jsonl(path)
    write_json(output, summary)
    return summary
