from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.io import write_json
from foi_o_nz.mcp_bundle import build_mcp_bundle, write_mcp_bundle
from foi_o_nz.oci_layout import materialise_oci_layout
from foi_o_nz.table_contracts import build_table_contracts, write_table_contracts


def test_table_contracts_include_duckdb_and_agent_boundary(tmp_path: Path) -> None:
    contracts = build_table_contracts()
    assert contracts["schema_version"] == "foi-o-nz.table-contracts.v0.1.0"
    requests = next(table for table in contracts["tables"] if table["name"] == "requests")
    assert "CREATE TABLE" in requests["duckdb_create_table_sql"]
    assert requests["agent_boundary"] == "analytical_contract_only_not_source_of_legal_truth"
    output = tmp_path / "contracts.json"
    result = write_table_contracts(output)
    assert result["table_count"] >= 5
    assert json.loads(output.read_text(encoding="utf-8"))["tables"]


def test_materialise_oci_layout_writes_index_and_blobs(tmp_path: Path) -> None:
    artefact = tmp_path / "artifact.json"
    write_json(artefact, {"ok": True})
    output_dir = tmp_path / "oci"
    result = materialise_oci_layout([artefact], output_dir, base_dir=tmp_path)
    assert result["artifact_count"] == 1
    assert (output_dir / "oci-layout").exists()
    assert (output_dir / "index.json").exists()
    index = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    digest = index["manifests"][0]["digest"].split(":", 1)[1]
    assert (output_dir / "blobs" / "sha256" / digest).exists()


def test_mcp_bundle_exports_resources_prompts_and_tools(tmp_path: Path) -> None:
    bundle = build_mcp_bundle()
    assert bundle["resources"]
    assert bundle["prompts"]
    assert any(tool["name"] == "map_state" for tool in bundle["tools"])
    output = tmp_path / "mcp.json"
    result = write_mcp_bundle(output)
    assert result["resource_count"] >= 1
    assert (
        json.loads(output.read_text(encoding="utf-8"))["schema_version"]
        == "foi-o-nz.mcp-bundle.v0.1.0"
    )
