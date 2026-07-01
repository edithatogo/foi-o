"""Optional LanceDB vector-index materialisation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import iter_jsonl


def build_lancedb_table(
    embeddings_jsonl: Path,
    *,
    database_dir: Path,
    table_name: str = "foi_o_nz_embeddings",
    mode: str = "overwrite",
) -> dict[str, Any]:
    """Create a LanceDB table from embedding JSONL.

    The function is optional by design. It raises a clear RuntimeError when the
    bleeding-edge vector stack is not installed in the active environment.
    """
    try:
        import lancedb  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("lancedb is required: install foi-o-nz[analytics]") from exc
    records = list(iter_jsonl(embeddings_jsonl))
    database_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(database_dir))
    if not records:
        return {"table_name": table_name, "row_count": 0, "database_dir": str(database_dir)}
    table = db.create_table(table_name, data=records, mode=mode)
    return {
        "table_name": table_name,
        "row_count": len(records),
        "database_dir": str(database_dir),
        "schema": str(table.schema),
    }
