from __future__ import annotations

from pathlib import Path

from foi_o_nz.schema_codegen import compare_committed_schemas, export_generated_schemas
from foi_o_nz.shacl_validation import validate_with_shacl


def test_export_generated_schemas(tmp_path: Path) -> None:
    result = export_generated_schemas(tmp_path)
    assert result["schema_count"] >= 4
    assert (tmp_path / "core-event.schema.json").exists()


def test_compare_committed_schemas() -> None:
    result = compare_committed_schemas(Path("schemas/json"))
    assert result["ok"]
    assert isinstance(result["findings"], list)


def test_validate_with_shacl_parse_only_or_full(tmp_path: Path) -> None:
    data = tmp_path / "data.ttl"
    shapes = tmp_path / "shapes.ttl"
    data.write_text("@prefix ex: <http://example/> . ex:s ex:p ex:o .\n", encoding="utf-8")
    shapes.write_text("@prefix sh: <http://www.w3.org/ns/shacl#> .\n", encoding="utf-8")
    result = validate_with_shacl(data, shapes)
    assert result["ok"] is True
    assert result["data_triples"] == 1
