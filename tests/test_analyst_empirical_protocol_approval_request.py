import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
REQUEST = ROOT / "examples/v2/analyst-empirical-protocol-approval.pending.json"
SCHEMA = ROOT / "schemas/json/analyst-empirical-protocol-approval-request.schema.json"


def test_pending_protocol_approval_request_is_valid_and_hash_pinned() -> None:
    result = validate_json_schema(REQUEST, SCHEMA)
    assert not result.errors, result.errors
    request = json.loads(REQUEST.read_text())
    protocol = ROOT / request["protocol"]["path"]
    assert request["protocol"]["sha256"] == sha256(protocol.read_bytes()).hexdigest()


def test_pending_request_does_not_authorize_sample_or_execution() -> None:
    request = json.loads(REQUEST.read_text())
    assert request["human_approval_present"] is False
    assert request["protocol_approved"] is False
    assert request["sample_membership_approved"] is False
    assert request["execution_allowed"] is False
    assert request["empirical_evidence"] is False
    assert request["human_reviewed"] is False
    assert request["gold_eligible"] is False
    assert all(value is False for value in request["prohibited_actions"].values())


def test_request_contains_exact_bounded_approval_statement() -> None:
    request = json.loads(REQUEST.read_text())
    statement = request["exact_approval_required"]
    assert request["protocol"]["sha256"] in statement
    assert request["protocol"]["repository_commit"] in statement
    assert "protocol design only" in statement
    assert "does not authorize sample membership" in statement
    assert "does not authorize analyst execution" in statement
