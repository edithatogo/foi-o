import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
RESULT = ROOT / "examples/v2/bounded-pilot-attachment-stderr-diagnostic-result.1.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-stderr-diagnostic-result.schema.json"


def test_diagnostic_result_is_valid_and_pins_execution_commit() -> None:
    validation = validate_json_schema(RESULT, SCHEMA)
    assert not validation.errors, validation.errors
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    for field in ("authorization", "diagnostic_request", "wrapper"):
        pin = result[field]
        historical = subprocess.run(
            ["git", "show", f"{result['repository_commit']}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert sha256(historical).hexdigest() == pin["sha256"]


def test_diagnostic_result_records_only_metadata_and_remains_fail_closed() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    observations = result["observations"]
    assert observations["stderr_fingerprint_reproduced_across_passes"] is True
    assert observations["stderr_content_reviewed"] is False
    assert result["postflight"]["derived_text_retained"] is False
    assert result["warning_policy_determined"] is False
    assert result["derivation_retry_authorized"] is False
    assert result["quarantine"]["content_committed"] is False
    for field in (
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert result[field] is False
