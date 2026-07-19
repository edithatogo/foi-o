import ast
import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.bounded_pilot_attachment_derivation import (
    build_attachment_derivation_execution_request,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-attachment-text-method-approval.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-text-method-approval.schema.json"
WRAPPER = ROOT / "src/foi_o_nz/bounded_pilot_attachment_derivation.py"


def test_method_approval_is_exact_and_fail_closed() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    assert (
        approval["approval_statement_sha256"]
        == sha256(approval["approval_statement"].encode("utf-8")).hexdigest()
    )
    candidate = ROOT / approval["approved_candidate"]["path"]
    assert approval["approved_candidate"]["sha256"] == sha256(candidate.read_bytes()).hexdigest()
    committed = subprocess.run(
        [
            "git",
            "show",
            f"{approval['approved_candidate']['repository_commit']}:{approval['approved_candidate']['path']}",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert approval["approved_candidate"]["sha256"] == sha256(committed).hexdigest()
    assert approval["method_approved"] is True
    assert approval["wrapper_creation_allowed"] is True
    assert approval["authorization_request_creation_allowed"] is True
    assert approval["pdf_processing_allowed"] is False
    assert approval["derived_content_creation_allowed"] is False
    assert approval["context_presentation_allowed"] is False
    assert approval["analyst_execution_allowed"] is False


def test_request_builder_is_inert_and_deterministic() -> None:
    digest = sha256(WRAPPER.read_bytes()).hexdigest()
    first = build_attachment_derivation_execution_request(
        repository_root=ROOT,
        wrapper_path="src/foi_o_nz/bounded_pilot_attachment_derivation.py",
        wrapper_sha256=digest,
    )
    second = build_attachment_derivation_execution_request(
        repository_root=ROOT,
        wrapper_path="src/foi_o_nz/bounded_pilot_attachment_derivation.py",
        wrapper_sha256=digest,
    )
    assert first == second
    assert len(first["sources"]) == 3
    assert first["authorization_present"] is False
    assert first["pdf_processing_allowed"] is False
    assert first["derived_content_creation_allowed"] is False


def test_inert_builder_has_no_process_execution_surface() -> None:
    tree = ast.parse(WRAPPER.read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "subprocess" not in imported
