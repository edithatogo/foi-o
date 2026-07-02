"""Optional LanceDB vector-index materialisation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.embeddings import hash_embedding
from foi_o_nz.io import iter_jsonl


def _load_lancedb() -> Any:
    import lancedb  # type: ignore[import-not-found]

    return lancedb


def lancedb_status() -> dict[str, Any]:
    """Return optional LanceDB runtime status."""
    try:
        _load_lancedb()
    except ModuleNotFoundError:
        return {
            "available": False,
            "mode": "degraded",
            "fallback_provider_id": "deterministic.feature_hash",
            "message": "lancedb is required: install foi-o-nz[analytics]",
            "legal_effect": "none",
            "machine_certification_allowed": False,
        }
    return {
        "available": True,
        "mode": "lancedb",
        "fallback_provider_id": "deterministic.feature_hash",
        "message": "LanceDB available for local fixture-backed vector retrieval.",
        "legal_effect": "none",
        "machine_certification_allowed": False,
    }


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
        lancedb = _load_lancedb()
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


def search_embedding_records(
    embeddings_jsonl: Path,
    *,
    query_text: str,
    database_dir: Path,
    table_name: str = "foi_o_nz_embeddings",
    top_k: int = 10,
    dimensions: int = 128,
) -> dict[str, Any]:
    """Search embedding records using LanceDB when available, else deterministic fallback."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    status = lancedb_status()
    if status["available"] is True:
        try:
            return _search_lancedb(
                query_text=query_text,
                database_dir=database_dir,
                table_name=table_name,
                top_k=top_k,
                dimensions=dimensions,
            )
        except Exception as exc:  # noqa: BLE001 - fallback preserves local search availability
            fallback = _search_deterministic(
                embeddings_jsonl,
                query_text=query_text,
                top_k=top_k,
                dimensions=dimensions,
            )
            fallback["fallback_reason"] = f"lancedb query failed: {exc}"
            return fallback
    fallback = _search_deterministic(
        embeddings_jsonl,
        query_text=query_text,
        top_k=top_k,
        dimensions=dimensions,
    )
    fallback["fallback_reason"] = status["message"]
    return fallback


def _search_lancedb(
    *,
    query_text: str,
    database_dir: Path,
    table_name: str,
    top_k: int,
    dimensions: int,
) -> dict[str, Any]:
    lancedb = _load_lancedb()
    db = lancedb.connect(str(database_dir))
    table = db.open_table(table_name)
    rows = table.search(hash_embedding(query_text, dimensions=dimensions)).limit(top_k).to_list()
    results = [_normalise_search_row(row, rank=index) for index, row in enumerate(rows, start=1)]
    return {
        "ok": True,
        "backend": "lancedb",
        "fallback": False,
        "query": query_text,
        "top_k": top_k,
        "dimensions": dimensions,
        "database_dir": str(database_dir),
        "table_name": table_name,
        "result_count": len(results),
        "provider_provenance": _retrieval_provenance(
            provider_id="lancedb.local",
            runtime="lancedb",
            fallback=False,
            message="Local LanceDB table queried with deterministic query embedding.",
        ),
        "results": results,
        "legal_effect": "none",
        "machine_certification_allowed": False,
    }


def _search_deterministic(
    embeddings_jsonl: Path,
    *,
    query_text: str,
    top_k: int,
    dimensions: int,
) -> dict[str, Any]:
    query_vector = hash_embedding(query_text, dimensions=dimensions)
    scored: list[tuple[float, dict[str, Any]]] = []
    for record in iter_jsonl(embeddings_jsonl):
        embedding = record.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != dimensions:
            continue
        vector = [float(value) for value in embedding]
        score = _cosine(query_vector, vector)
        scored.append((score, record))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("source_id") or "")))
    results = [
        _normalise_search_row(record, rank=index, score=score)
        for index, (score, record) in enumerate(scored[:top_k], start=1)
    ]
    return {
        "ok": True,
        "backend": "deterministic.feature_hash",
        "fallback": True,
        "query": query_text,
        "top_k": top_k,
        "dimensions": dimensions,
        "database_dir": None,
        "table_name": None,
        "result_count": len(results),
        "provider_provenance": _retrieval_provenance(
            provider_id="deterministic.feature_hash",
            runtime="python",
            fallback=True,
            message="Deterministic in-memory embedding search fallback.",
        ),
        "results": results,
        "legal_effect": "none",
        "machine_certification_allowed": False,
    }


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    return sum(a * b for a, b in zip(left, right, strict=True))


def _normalise_search_row(
    row: dict[str, Any], *, rank: int, score: float | None = None
) -> dict[str, Any]:
    distance = row.get("_distance")
    resolved_score = score
    if resolved_score is None and isinstance(distance, int | float):
        resolved_score = 1.0 / (1.0 + float(distance))
    if resolved_score is None:
        resolved_score = 0.0
    return {
        "rank": rank,
        "source_id": str(row.get("source_id") or "unknown"),
        "kind": row.get("kind"),
        "text": row.get("text"),
        "score": round(float(resolved_score), 8),
        "embedding_provider": row.get("embedding_provider"),
        "metadata": row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
        "provider_provenance": row.get("provider_provenance")
        if isinstance(row.get("provider_provenance"), dict)
        else {},
    }


def _retrieval_provenance(
    *, provider_id: str, runtime: str, fallback: bool, message: str
) -> dict[str, Any]:
    return {
        "provider_id": provider_id,
        "runtime": runtime,
        "fallback": fallback,
        "legal_effect": "none",
        "machine_certification_allowed": False,
        "message": message,
    }
