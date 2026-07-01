from __future__ import annotations

from pathlib import Path

from foi_o_nz.kernel_fallback import (
    assertion_status_rank,
    can_agent_assert_status,
    confidence_band,
    stable_text_bucket,
)
from foi_o_nz.kernel_manifest import (
    build_conformance_fixture_records,
    build_kernel_manifest,
    build_kernel_readiness,
    write_kernel_fixtures,
    write_kernel_manifest,
    write_kernel_readiness,
)
from foi_o_nz.mojo_audit import build_mojo_audit, write_mojo_audit
from foi_o_nz.validation import validate_json_schema


def test_new_epistemic_fallback_operations() -> None:
    assert assertion_status_rank("unknown") == 0
    assert assertion_status_rank("certified") == 4
    assert assertion_status_rank("future") == -1
    assert confidence_band(0.0) == "none"
    assert confidence_band(0.74) == "medium"
    assert confidence_band(0.95) == "high"
    assert can_agent_assert_status("observed") is True
    assert can_agent_assert_status("certified") is False
    assert stable_text_bucket("foi-o-nz", 16) == 12
    assert stable_text_bucket("foi-o-nz", 0) == 0


def test_static_mojo_audit_has_all_expected_declarations(tmp_path: Path) -> None:
    report_path = tmp_path / "mojo-audit.json"
    report = write_mojo_audit(report_path)
    assert report["schema_version"] == "foi-o-nz.mojo-audit.v0.1.0"
    assert report["ok"] is True
    assert report["missing_expected_operations"] == []
    validation = validate_json_schema(report_path, Path("schemas/json/mojo-audit.schema.json"))
    assert validation.ok, validation.errors


def test_kernel_manifest_and_readiness_validate(tmp_path: Path) -> None:
    manifest_path = tmp_path / "kernel-manifest.json"
    readiness_path = tmp_path / "kernel-readiness.json"
    manifest = write_kernel_manifest(manifest_path)
    readiness = write_kernel_readiness(readiness_path)
    assert manifest["operation_count"] >= 27
    assert manifest["mojo_declared_operation_count"] == manifest["operation_count"]
    assert readiness["ok_for_python_fallback"] is True
    assert readiness["ok_for_static_mojo_source"] is True
    assert readiness["ok_for_native_release"] is False
    for path, schema in [
        (manifest_path, Path("schemas/json/kernel-manifest.schema.json")),
        (readiness_path, Path("schemas/json/kernel-readiness.schema.json")),
    ]:
        validation = validate_json_schema(path, schema)
        assert validation.ok, validation.errors


def test_kernel_fixture_export(tmp_path: Path) -> None:
    fixture_path = tmp_path / "kernel-fixtures.jsonl"
    records = write_kernel_fixtures(fixture_path)
    assert len(records) == len(build_conformance_fixture_records())
    assert fixture_path.read_text(encoding="utf-8").count("\n") == len(records)
    assert records[0]["case_id"].startswith("kernel-case-")


def test_in_memory_reports_are_consistent() -> None:
    audit = build_mojo_audit()
    manifest = build_kernel_manifest()
    readiness = build_kernel_readiness()
    assert audit["declared_expected_count"] == manifest["mojo_declared_operation_count"]
    assert readiness["operation_count"] == manifest["operation_count"]
