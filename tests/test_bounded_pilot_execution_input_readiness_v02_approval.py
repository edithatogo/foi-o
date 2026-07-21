import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-execution-input-readiness-v0.2-approval.approved.json"
APPROVAL_SCHEMA = (
    ROOT / "schemas/json/bounded-pilot-execution-input-readiness-v0.2-approval.schema.json"
)
READINESS = ROOT / "examples/v2/bounded-pilot-execution-input-readiness.v0.2.approved.json"
READINESS_SCHEMA = (
    ROOT / "schemas/json/bounded-pilot-execution-input-readiness-v0.2-approved.schema.json"
)


def test_readiness_approval_is_exact_and_candidate_bound() -> None:
    result = validate_json_schema(APPROVAL, APPROVAL_SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(APPROVAL.read_text())
    assert (
        sha256(approval["approval_statement"].encode()).hexdigest()
        == approval["approval_statement_sha256"]
    )
    pin = approval["approved_candidate"]
    assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]


def test_approved_readiness_still_prohibits_access_and_execution() -> None:
    result = validate_json_schema(READINESS, READINESS_SCHEMA)
    assert not result.errors, result.errors
    readiness = json.loads(READINESS.read_text())
    assert readiness["inputs_ready"] is True
    assert (
        sha256((ROOT / readiness["approval"]["path"]).read_bytes()).hexdigest()
        == readiness["approval"]["sha256"]
    )
    for key in (
        "derived_text_read_allowed",
        "context_materialization_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "execution_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert readiness[key] is False
