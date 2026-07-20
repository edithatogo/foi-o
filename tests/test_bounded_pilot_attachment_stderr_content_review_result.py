import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
RESULT = ROOT / "examples/v2/bounded-pilot-attachment-stderr-content-review-result.1.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-stderr-content-review-result.schema.json"


def test_stderr_content_review_result_is_valid_and_pins_review_chain() -> None:
    validation = validate_json_schema(RESULT, SCHEMA)
    assert not validation.errors, validation.errors
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    for field in ("review_request", "review_approval"):
        pin = result[field]
        historical = subprocess.run(
            ["git", "show", f"{result['repository_commit']}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert sha256(historical).hexdigest() == pin["sha256"]


def test_stderr_content_review_result_blocks_retry_and_contains_no_content() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["classification"] == "error_signal_present"
    assert result["category_counts_per_file"] == {"error_signal": 3}
    assert result["verbatim_stderr_emitted"] is False
    assert result["verbatim_stderr_committed"] is False
    assert result["warning_policy_candidate"] is False
    assert result["derivation_retry_authorized"] is False
    assert result["derived_text_reviewed"] is False
