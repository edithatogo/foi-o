import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
METHOD = ROOT / "examples/v2/bounded-pilot-attachment-alternative-text-method.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-alternative-text-method.schema.json"


def test_alternative_method_is_valid_and_pins_prior_evidence() -> None:
    validation = validate_json_schema(METHOD, SCHEMA)
    assert not validation.errors, validation.errors
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    for field in (
        "input_approval",
        "evidence_manifest",
        "superseded_method",
        "stderr_review_result",
    ):
        pin = method[field]
        assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]


def test_alternative_method_pins_independent_runtime_without_processing() -> None:
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    runtime = method["runtime_observation"]
    assert (
        sha256(Path(runtime["resolved_path"]).read_bytes()).hexdigest()
        == runtime["executable_sha256"]
    )
    assert method["argv_template"] == [
        "mutool",
        "draw",
        "-q",
        "-F",
        "txt",
        "-o",
        "<output>",
        "<input>",
    ]
    assert method["method_difference"]["independent_parser"] is True
    assert method["failure_contract"]["ignore_errors_option_allowed"] is False


def test_alternative_method_is_inert_and_fail_closed() -> None:
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    assert method["failure_contract"]["all_or_nothing"] is True
    assert method["failure_contract"]["ocr_fallback_allowed"] is False
    assert method["failure_contract"]["pdf_repair_allowed"] is False
    for field in (
        "method_approved",
        "runtime_approved",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert method[field] is False
