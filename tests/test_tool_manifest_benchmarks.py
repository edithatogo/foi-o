from __future__ import annotations

from pathlib import Path

from foi_o_nz.benchmarks import run_local_benchmarks, write_local_benchmarks
from foi_o_nz.tool_manifest import build_tool_manifest, write_tool_manifest


def test_tool_manifest_preserves_agent_boundaries(tmp_path: Path) -> None:
    manifest = build_tool_manifest()
    assert manifest["tools"]
    assert all(tool["machine_certification_allowed"] is False for tool in manifest["tools"])
    assert any("No autonomous" in item for item in manifest["global_boundaries"])

    output = tmp_path / "tool-manifest.json"
    result = write_tool_manifest(output)
    assert result["tool_count"] == len(manifest["tools"])
    assert output.exists()


def test_local_benchmarks_emit_rates(tmp_path: Path) -> None:
    result = run_local_benchmarks(iterations=10)
    assert result["iterations"] == 10
    assert set(result["benchmarks"]) == {"map_state", "chunk_request", "ledger_hash", "risk_scan"}
    assert result["benchmarks"]["map_state"]["records_per_second"] > 0

    output = tmp_path / "benchmarks.json"
    write_result = write_local_benchmarks(output, iterations=10)
    assert write_result["ok"] is True
    assert output.exists()


def test_tool_version_runtime_error_handled(monkeypatch) -> None:
    import shutil
    import subprocess

    from foi_o_nz.reproducibility import tool_version

    monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/dummy")

    def mock_run(*_args, **_kwargs):
        raise RuntimeError("simulated error")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = tool_version("dummy_tool", "--version")
    assert result.name == "dummy_tool"
    assert result.available is True
    assert result.executable == "/usr/bin/dummy"
    assert result.version_output is not None
    assert "version check failed: simulated error" in result.version_output
