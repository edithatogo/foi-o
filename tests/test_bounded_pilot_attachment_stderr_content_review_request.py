import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/bounded-pilot-attachment-stderr-content-review-request.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-stderr-content-review-request.schema.json"


def test_stderr_content_review_request_is_valid_and_pins_result() -> None:
    validation = validate_json_schema(REQUEST, SCHEMA)
    assert not validation.errors, validation.errors
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    pin = request["diagnostic_result"]
    historical = subprocess.run(
        ["git", "show", f"{request['diagnostic_result_commit']}:{pin['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert sha256(historical).hexdigest() == pin["sha256"]


def test_stderr_content_review_request_is_inert_and_non_derivational() -> None:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert request["review_output_contract"] == "metadata_only_classification_no_verbatim_stderr"
    for field in (
        "authorization_present",
        "stderr_content_review_allowed",
        "derived_text_review_allowed",
        "derivation_retry_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert request[field] is False
