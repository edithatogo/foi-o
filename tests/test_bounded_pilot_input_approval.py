import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-input-approval.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-input-approval.schema.json"


def test_input_approval_is_valid_and_pins_exact_artifacts_and_statement() -> None:
    result = validate_json_schema(APPROVAL, SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    for pin in approval["approved_artifacts"].values():
        assert pin["sha256"] == sha256((ROOT / pin["path"]).read_bytes()).hexdigest()
        committed = subprocess.run(
            ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert pin["sha256"] == sha256(committed).hexdigest()
    assert (
        approval["approval_statement_sha256"]
        == sha256(approval["approval_statement"].encode("utf-8")).hexdigest()
    )


def test_input_approval_remains_fail_closed_for_execution_and_claims() -> None:
    approval = json.loads(APPROVAL.read_text())
    assert approval["evidence_census_approved"] is True
    assert approval["blinded_codebook_approved"] is True
    assert approval["approved_purpose"] == "bounded_local_execution_input_promotion_only"
    assert approval["approved_scope"] == {
        "correspondence_block_count": 5,
        "request_11872_attachment_count": 3,
        "request_35076_empty_attachment_inventory": True,
        "vocabulary_state_count": 17,
        "decision_rules_approved": True,
    }
    assert approval["context_presentation_allowed"] is False
    assert approval["execution_allowed"] is False
    assert approval["reconciliation_allowed"] is False
    assert approval["empirical_result_approval"] is False
    assert approval["population_inference_allowed"] is False
    assert approval["archive_wide_claim_allowed"] is False
    assert approval["empirical_evidence"] is False
    assert approval["human_reviewed"] is False
    assert approval["gold_eligible"] is False
    assert approval["legal_certified"] is False
    assert approval["separate_execution_authorization_required"] is True
    assert approval["clean_head_pre_execution_verification_required"] is True
