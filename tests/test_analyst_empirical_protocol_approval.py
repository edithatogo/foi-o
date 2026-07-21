import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/analyst-empirical-protocol-approval.approved.json"
SCHEMA = ROOT / "schemas/json/analyst-empirical-protocol-approval.schema.json"


def test_protocol_approval_is_valid_and_pins_exact_request() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    request = ROOT / approval["approved_request"]["path"]
    assert approval["approved_request"]["sha256"] == sha256(request.read_bytes()).hexdigest()
    statement = approval["approval_statement"].encode()
    assert approval["approval_statement_sha256"] == sha256(statement).hexdigest()


def test_protocol_approval_does_not_expand_scope() -> None:
    approval = json.loads(APPROVAL.read_text())
    assert approval["protocol_approved"] is True
    assert approval["sample_membership_approved"] is False
    assert approval["execution_allowed"] is False
    assert approval["empirical_evidence"] is False
    assert approval["human_reviewed"] is False
    assert approval["gold_eligible"] is False
    assert all(value is False for value in approval["prohibited_actions"].values())
