from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from foi_o_nz import vector_index
from foi_o_nz.cli import app
from foi_o_nz.embeddings import embedding_record
from foi_o_nz.io import write_jsonl

RUNNER = CliRunner()


def _embedding_jsonl(path: Path) -> Path:
    records = [
        embedding_record(
            {"request_id": "1", "title": "Health data and hospital policy", "authority": "A"},
            kind="request",
            dimensions=8,
        ),
        embedding_record(
            {"request_id": "2", "title": "Transport timetables", "authority": "B"},
            kind="request",
            dimensions=8,
        ),
    ]
    write_jsonl(path, records)
    return path


def test_lancedb_status_degrades_when_dependency_missing(monkeypatch) -> None:
    def missing_lancedb():
        raise ModuleNotFoundError("lancedb")

    monkeypatch.setattr(vector_index, "_load_lancedb", missing_lancedb)

    status = vector_index.lancedb_status()

    assert status["available"] is False
    assert status["mode"] == "degraded"
    assert status["fallback_provider_id"] == "deterministic.feature_hash"
    assert "install foi-o-nz[analytics]" in status["message"]


def test_embedding_search_falls_back_without_lancedb(tmp_path: Path, monkeypatch) -> None:
    def missing_lancedb():
        raise ModuleNotFoundError("lancedb")

    monkeypatch.setattr(vector_index, "_load_lancedb", missing_lancedb)
    embeddings = _embedding_jsonl(tmp_path / "embeddings.jsonl")

    result = vector_index.search_embedding_records(
        embeddings,
        query_text="health hospital",
        database_dir=tmp_path / "lancedb",
        top_k=1,
        dimensions=8,
    )

    assert result["ok"] is True
    assert result["backend"] == "deterministic.feature_hash"
    assert result["fallback"] is True
    assert result["result_count"] == 1
    assert result["results"][0]["source_id"] == "1"
    assert result["provider_provenance"]["machine_certification_allowed"] is False


def test_lancedb_table_query_uses_fixture_embeddings_when_available(tmp_path: Path) -> None:
    if vector_index.lancedb_status()["available"] is not True:
        pytest.skip("LanceDB is not installed")
    embeddings = _embedding_jsonl(tmp_path / "embeddings.jsonl")
    database_dir = tmp_path / "lancedb"

    table_result = vector_index.build_lancedb_table(embeddings, database_dir=database_dir)
    search_result = vector_index.search_embedding_records(
        embeddings,
        query_text="health hospital",
        database_dir=database_dir,
        top_k=1,
        dimensions=8,
    )

    assert table_result["row_count"] == 2
    assert search_result["ok"] is True
    assert search_result["backend"] == "lancedb"
    assert search_result["fallback"] is False
    assert search_result["result_count"] == 1
    assert search_result["results"][0]["source_id"] == "1"


def test_search_lancedb_cli_returns_fallback_results_without_dependency(
    tmp_path: Path, monkeypatch
) -> None:
    def missing_lancedb():
        raise ModuleNotFoundError("lancedb")

    monkeypatch.setattr(vector_index, "_load_lancedb", missing_lancedb)
    embeddings = _embedding_jsonl(tmp_path / "embeddings.jsonl")

    result = RUNNER.invoke(
        app,
        [
            "search-lancedb",
            str(embeddings),
            "--query",
            "health hospital",
            "--database-dir",
            str(tmp_path / "lancedb"),
            "--top-k",
            "1",
            "--dimensions",
            "8",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["backend"] == "deterministic.feature_hash"
    assert payload["fallback"] is True
    assert payload["results"][0]["source_id"] == "1"
    assert payload["machine_certification_allowed"] is False
