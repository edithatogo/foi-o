import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
METHOD = ROOT / "examples/v2/bounded-pilot-attachment-text-method.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-text-method.schema.json"


def test_attachment_text_method_is_valid_and_pins_census_sources() -> None:
    result = validate_json_schema(METHOD, SCHEMA)
    assert not result.errors, result.errors
    method = json.loads(METHOD.read_text())
    pin = method["evidence_manifest"]
    evidence_path = ROOT / pin["path"]
    assert pin["sha256"] == sha256(evidence_path.read_bytes()).hexdigest()
    evidence = json.loads(evidence_path.read_text())
    record = next(item for item in evidence["records"] if item["request_id"] == "11872")
    expected = record["attachments"]["files"]
    for index, (source, census_source) in enumerate(zip(method["sources"], expected, strict=True)):
        assert {key: source[key] for key in census_source} == census_source
        assert source["output_name"] == f"attachment-{index:03d}.txt"


def test_attachment_text_method_pins_local_tool_and_exact_argv() -> None:
    method = json.loads(METHOD.read_text())
    runtime = method["runtime_observation"]
    executable = Path(runtime["resolved_path"])
    assert runtime["executable_sha256"] == sha256(executable.read_bytes()).hexdigest()
    assert method["argv_template"] == [
        "pdftotext",
        "-layout",
        "-enc",
        "UTF-8",
        "-eol",
        "unix",
        "<input>",
        "<output>",
    ]


def test_attachment_text_method_is_inert_and_fail_closed() -> None:
    method = json.loads(METHOD.read_text())
    assert method["failure_contract"]["all_or_nothing"] is True
    assert method["failure_contract"]["partial_readiness_allowed"] is False
    assert method["failure_contract"]["ocr_fallback_allowed"] is False
    assert method["output_contract"]["content_committed"] is False
    assert method["restricted_outputs_committed"] is False
    assert method["method_approved"] is False
    assert method["runtime_approved"] is False
    assert method["derivation_allowed"] is False
    assert method["context_presentation_allowed"] is False
    assert method["analyst_execution_allowed"] is False
    assert method["empirical_evidence"] is False
    assert method["human_reviewed"] is False
    assert method["gold_eligible"] is False
