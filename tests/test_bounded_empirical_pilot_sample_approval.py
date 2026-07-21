import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-empirical-pilot-sample.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-empirical-pilot-sample-approval.schema.json"


def test_approval_is_valid_and_pins_candidate_and_statement() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    candidate = ROOT / approval["approved_candidate"]["path"]
    assert approval["approved_candidate"]["sha256"] == sha256(candidate.read_bytes()).hexdigest()
    assert (
        approval["approval_statement_sha256"]
        == sha256(approval["approval_statement"].encode()).hexdigest()
    )


def test_approval_expands_only_local_pilot_purpose() -> None:
    approval = json.loads(APPROVAL.read_text())
    assert approval["sample_membership_approved"] is True
    assert approval["purpose_rights_approved"] is True
    assert approval["approved_members"] == ["11872", "35076"]
    assert approval["execution_allowed"] is False
    assert approval["context_presentation_allowed"] is False
    assert approval["population_inference_allowed"] is False
    assert approval["archive_wide_claim_allowed"] is False
    assert approval["empirical_evidence"] is False
