import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.bounded_pilot_attachment_derivation import (
    build_attachment_derivation_execution_request,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/bounded-pilot-attachment-derivation-execution-request.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-derivation-execution-request.schema.json"


def test_execution_request_is_valid_deterministic_and_pinned() -> None:
    result = validate_json_schema(REQUEST, SCHEMA)
    assert not result.errors, result.errors
    request = json.loads(REQUEST.read_text())
    built = build_attachment_derivation_execution_request(
        repository_root=ROOT,
        wrapper_path=request["wrapper"]["path"],
        wrapper_sha256=request["wrapper"]["sha256"],
    )
    assert {key: request[key] for key in built} == built
    for key in ("method", "method_approval"):
        assert (
            request[key]["sha256"] == sha256((ROOT / request[key]["path"]).read_bytes()).hexdigest()
        )
    committed_wrapper = subprocess.run(
        ["git", "show", f"{request['wrapper_repository_commit']}:{request['wrapper']['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert request["wrapper"]["sha256"] == sha256(committed_wrapper).hexdigest()


def test_execution_request_remains_inert() -> None:
    request = json.loads(REQUEST.read_text())
    assert request["authorization_present"] is False
    assert request["pdf_processing_allowed"] is False
    assert request["derived_content_creation_allowed"] is False
    assert request["context_presentation_allowed"] is False
    assert request["analyst_execution_allowed"] is False
    assert request["reconciliation_allowed"] is False
    assert request["empirical_evidence"] is False
    assert request["human_reviewed"] is False
    assert request["gold_eligible"] is False
