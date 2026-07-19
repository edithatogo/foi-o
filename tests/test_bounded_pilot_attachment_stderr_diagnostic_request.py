import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/bounded-pilot-attachment-stderr-diagnostic-request.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-stderr-diagnostic-request.schema.json"


def test_diagnostic_request_is_valid_and_pins_historical_wrapper() -> None:
    result = validate_json_schema(REQUEST, SCHEMA)
    assert not result.errors, result.errors
    request = json.loads(REQUEST.read_text())
    failure = request["prior_failure"]
    assert failure["sha256"] == sha256((ROOT / failure["path"]).read_bytes()).hexdigest()
    wrapper = subprocess.run(
        ["git", "show", f"{request['wrapper_repository_commit']}:{request['wrapper']['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert request["wrapper"]["sha256"] == sha256(wrapper).hexdigest()


def test_diagnostic_request_is_inert_and_retains_no_derived_text() -> None:
    request = json.loads(REQUEST.read_text())
    assert request["authorization_present"] is False
    assert request["pdf_processing_allowed"] is False
    assert request["derived_text_install_allowed"] is False
    assert request["diagnostic_quarantine_policy"]["retain_stderr_only"] is True
    assert request["diagnostic_quarantine_policy"]["retain_derived_text"] is False
    assert request["context_presentation_allowed"] is False
    assert request["analyst_execution_allowed"] is False
    assert request["empirical_evidence"] is False
