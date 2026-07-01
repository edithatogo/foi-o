"""Optional DuckDB materialisation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_duckdb_database(
    *,
    database: Path,
    requests_jsonl: Path | None = None,
    events_jsonl: Path | None = None,
    requests_parquet: Path | None = None,
    events_parquet: Path | None = None,
) -> dict[str, Any]:
    """Materialise JSONL/Parquet request and event tables into DuckDB."""
    try:
        import duckdb  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("duckdb optional dependency is required for this command") from exc

    database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database))
    tables: list[str] = []
    if requests_parquet is not None:
        con.execute("CREATE OR REPLACE TABLE requests AS SELECT * FROM read_parquet(?)", [str(requests_parquet)])
        tables.append("requests")
    elif requests_jsonl is not None:
        con.execute("CREATE OR REPLACE TABLE requests AS SELECT * FROM read_json_auto(?)", [str(requests_jsonl)])
        tables.append("requests")
    if events_parquet is not None:
        con.execute("CREATE OR REPLACE TABLE events AS SELECT * FROM read_parquet(?)", [str(events_parquet)])
        tables.append("events")
    elif events_jsonl is not None:
        con.execute("CREATE OR REPLACE TABLE events AS SELECT * FROM read_json_auto(?)", [str(events_jsonl)])
        tables.append("events")
    counts = {
        table: con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608 table comes from fixed list
        for table in tables
    }
    con.close()
    return {"database": str(database), "tables": tables, "counts": counts}


def write_duckdb_bootstrap_sql(output: Path) -> None:
    """Write a portable SQL bootstrap template for operators without Python extras."""
    output.parent.mkdir(parents=True, exist_ok=True)
    sql = """-- FOI-O NZ DuckDB bootstrap template
-- Replace paths with local JSONL or Parquet exports.
CREATE OR REPLACE TABLE requests AS SELECT * FROM read_json_auto('data/requests.jsonl');
CREATE OR REPLACE TABLE events AS SELECT * FROM read_json_auto('data/events.jsonl');
SELECT normalised_state, count(*) AS n FROM requests GROUP BY normalised_state ORDER BY n DESC;
"""
    output.write_text(sql, encoding="utf-8")
