import json
import subprocess
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
APPROVAL = (
    ROOT / "examples/v2/bounded-pilot-attachment-alternative-text-method-approval.approved.json"
)
SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-alternative-text-method-approval.schema.json"


def test_alternative_method_approval_is_valid_and_exact() -> None:
    validation = validate_json_schema(APPROVAL, SCHEMA)
    assert not validation.errors, validation.errors
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert (
        sha256(approval["approval_statement"].encode()).hexdigest()
        == approval["approval_statement_sha256"]
    )
    pin = approval["approved_candidate"]
    assert sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    committed = subprocess.run(
        ["git", "show", f"{pin['repository_commit']}:{pin['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert sha256(committed).hexdigest() == pin["sha256"]


def test_alternative_method_approval_only_allows_wrapper_and_request_creation() -> None:
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    assert approval["method_approved"] is True
    assert approval["wrapper_creation_allowed"] is True
    assert approval["authorization_request_creation_allowed"] is True
    assert len(approval["prohibited_actions"]) == 16
    for field in (
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert approval[field] is False
