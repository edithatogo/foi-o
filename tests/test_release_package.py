from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.release_package import (
    REQUIRED_RELEASE_VALIDATION_COMMANDS,
    validate_release_checklist_document,
)
from foi_o_nz.validation import validate_json_schema


CHECKLIST_EXAMPLE = Path("examples/release-checklist.v0.9.0.json")
CHECKLIST_SCHEMA = Path("schemas/json/release-checklist.schema.json")


def _load_checklist(path: Path = CHECKLIST_EXAMPLE) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_checklist_example_references_existing_evidence_and_external_gates() -> None:
    assert CHECKLIST_SCHEMA.exists()
    assert CHECKLIST_EXAMPLE.exists()

    schema_errors = validate_json_schema(CHECKLIST_EXAMPLE, CHECKLIST_SCHEMA).errors
    assert schema_errors == []

    validation = validate_release_checklist_document(CHECKLIST_EXAMPLE, base_dir=Path("."))
    assert validation["ok"] is True, validation["errors"]

    checklist = _load_checklist()
    commands = {item["command"] for item in checklist["validation_commands"]}
    for command in REQUIRED_RELEASE_VALIDATION_COMMANDS:
        assert command in commands

    evidence_paths = [Path(item["path"]) for item in checklist["evidence"]]
    assert Path("docs/19-release-readiness-evidence.md") in evidence_paths
    assert Path("examples/dataset-metadata.examples.json") in evidence_paths
    assert all(path.exists() for path in evidence_paths)

    gate_statuses = {item["status"] for item in checklist["external_gates"]}
    assert gate_statuses <= {"external_gate", "manual_approval_required"}
    assert "manual_approval_required" in gate_statuses

    rights_notice = checklist["rights_notice"]
    assert "MIT" in rights_notice
    assert "original rights" in rights_notice


def test_release_checklist_validation_reports_missing_evidence(tmp_path: Path) -> None:
    checklist = _load_checklist()
    checklist["evidence"].append(
        {
            "path": "docs/does-not-exist.md",
            "description": "Synthetic missing path for validation test.",
            "required": True,
        }
    )
    broken = tmp_path / "release-checklist.missing.json"
    broken.write_text(json.dumps(checklist), encoding="utf-8")

    validation = validate_release_checklist_document(broken, base_dir=Path("."))

    assert validation["ok"] is False
    assert any("docs/does-not-exist.md" in error for error in validation["errors"])
