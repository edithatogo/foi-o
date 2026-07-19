import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/bounded-pilot-attachment-mutool-execution-request.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-mutool-execution-request.schema.json"
METHOD = ROOT / "examples/v2/bounded-pilot-attachment-alternative-text-method.pending.json"


def test_mutool_execution_request_is_closed_valid_and_exactly_pinned() -> None:
    result = validate_json_schema(REQUEST, SCHEMA)
    assert not result.errors, result.errors
    request = json.loads(REQUEST.read_text())
    for key in ("method", "method_approval", "wrapper"):
        pin = request[key]
        assert pin["sha256"] == sha256((ROOT / pin["path"]).read_bytes()).hexdigest()

    committed_wrapper = subprocess.run(
        ["git", "show", f"{request['wrapper_repository_commit']}:{request['wrapper']['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert request["wrapper"]["sha256"] == sha256(committed_wrapper).hexdigest()
    assert committed_wrapper == (ROOT / request["wrapper"]["path"]).read_bytes()


def test_mutool_execution_request_matches_approved_method_semantics() -> None:
    request = json.loads(REQUEST.read_text())
    method = json.loads(METHOD.read_text())
    for key in (
        "sources",
        "method_tool",
        "runtime_observation",
        "environment",
        "argv_template",
        "output_contract",
        "failure_contract",
    ):
        assert request[key] == method[key]


def test_mutool_execution_request_remains_inert() -> None:
    request = json.loads(REQUEST.read_text())
    assert set(request) == {
        "schema_version",
        "request_id",
        "status",
        "method",
        "method_approval",
        "wrapper",
        "wrapper_repository_commit",
        "source_root",
        "output_directory",
        "sources",
        "method_tool",
        "runtime_observation",
        "environment",
        "argv_template",
        "output_contract",
        "failure_contract",
        "requested_scope",
        "authorization_present",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    }
    for key in (
        "authorization_present",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert request[key] is False

    source = Path(request["source_root"])
    output = Path(request["output_directory"])
    assert source.is_absolute()
    assert output.is_absolute()
    assert not source.is_relative_to(ROOT)
    assert not output.is_relative_to(ROOT)
    assert source != output
    assert not output.exists()
