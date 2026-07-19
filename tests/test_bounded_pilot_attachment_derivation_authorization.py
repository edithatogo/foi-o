import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.bounded_pilot_attachment_derivation import PROHIBITED_ACTIONS
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
HUMAN = ROOT / "examples/v2/bounded-pilot-attachment-derivation-human-approval.approved.json"
HUMAN_SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-derivation-human-approval.schema.json"
AUTH = (
    ROOT / "examples/v2/bounded-pilot-attachment-derivation-execution-authorization.approved.json"
)
AUTH_SCHEMA = (
    ROOT / "schemas/json/bounded-pilot-attachment-derivation-execution-authorization.schema.json"
)


def test_human_approval_is_exact_and_pins_request() -> None:
    result = validate_json_schema(HUMAN, HUMAN_SCHEMA)
    assert not result.errors, result.errors
    human = json.loads(HUMAN.read_text())
    assert (
        human["approval_statement_sha256"]
        == sha256(human["approval_statement"].encode("utf-8")).hexdigest()
    )
    assert human["prohibited_actions"] == PROHIBITED_ACTIONS
    pin = human["approved_request"]
    assert pin["sha256"] == sha256((ROOT / pin["path"]).read_bytes()).hexdigest()


def test_execution_authorization_is_exact_and_all_pins_match() -> None:
    result = validate_json_schema(AUTH, AUTH_SCHEMA)
    assert not result.errors, result.errors
    authorization = json.loads(AUTH.read_text())
    for key in ("execution_request", "wrapper", "method", "method_approval", "human_approval"):
        pin = authorization[key]
        assert pin["sha256"] == sha256((ROOT / pin["path"]).read_bytes()).hexdigest()
    assert authorization["authorization_effective"] is True
    assert authorization["pdf_processing_allowed"] is True
    assert authorization["derived_content_creation_allowed"] is True
    assert authorization["context_presentation_allowed"] is False
    assert authorization["analyst_execution_allowed"] is False
    assert authorization["reconciliation_allowed"] is False
    assert authorization["empirical_evidence"] is False
    assert authorization["human_reviewed"] is False
    assert authorization["gold_eligible"] is False
