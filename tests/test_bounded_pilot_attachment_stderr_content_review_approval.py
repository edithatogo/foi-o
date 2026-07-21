import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = ROOT / "examples/v2/bounded-pilot-attachment-stderr-content-review.approved.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-stderr-content-review-approval.schema.json"


def test_stderr_content_review_approval_is_valid_and_exact() -> None:
    validation = validate_json_schema(APPROVAL, SCHEMA)
    assert not validation.errors, validation.errors
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert (
        sha256(approval["approval_statement"].encode()).hexdigest()
        == approval["approval_statement_sha256"]
    )
    pin = approval["approved_request"]
    request = ROOT / pin["path"]
    assert sha256(request.read_bytes()).hexdigest() == pin["sha256"]
    assert pin["repository_commit"] == "26f2e159b26455843ef3b9522e75daef1d0bc7a2"


def test_stderr_content_review_approval_does_not_authorize_downstream_actions() -> None:
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert approval["stderr_content_review_allowed"] is True
    assert len(approval["prohibited_actions"]) == 16
    for field in (
        "derived_text_review_allowed",
        "derivation_retry_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert approval[field] is False
