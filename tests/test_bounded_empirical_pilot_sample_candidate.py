import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
CANDIDATE = ROOT / "examples/v2/bounded-empirical-pilot-sample.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-empirical-pilot-sample-candidate.schema.json"


def test_candidate_is_valid_and_all_evidence_pins_match() -> None:
    result = validate_json_schema(CANDIDATE, SCHEMA)
    assert not result.errors, result.errors
    candidate = json.loads(CANDIDATE.read_text())
    for member in candidate["members"]:
        for pin in member["evidence"]:
            path = ROOT / pin["path"]
            assert pin["sha256"] == sha256(path.read_bytes()).hexdigest()


def test_candidate_is_two_case_local_pilot_only() -> None:
    candidate = json.loads(CANDIDATE.read_text())
    assert [member["request_id"] for member in candidate["members"]] == ["11872", "35076"]
    assert candidate["sample_kind"] == "purposive_bounded_case_pilot"
    assert candidate["population_inference_allowed"] is False
    assert candidate["archive_wide_claim_allowed"] is False
    assert candidate["sample_membership_approved"] is False
    assert candidate["purpose_rights_approved"] is False
    assert candidate["execution_allowed"] is False


def test_candidate_records_required_purpose_expansion() -> None:
    candidate = json.loads(CANDIDATE.read_text())
    purposes = {member["request_id"]: member for member in candidate["members"]}
    assert purposes["11872"]["existing_approved_purpose"] == "local_raw_state_mapping_audit_only"
    assert purposes["35076"]["existing_approved_purpose"] == "local_candidate_extraction_only"
    assert all(member["purpose_expansion_required"] for member in candidate["members"])
    assert all(
        member["requested_purpose"] == "bounded_local_agent_empirical_pilot"
        for member in candidate["members"]
    )
