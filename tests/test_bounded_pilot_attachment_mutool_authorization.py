import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.bounded_pilot_attachment_mutool_derivation import PROHIBITED_ACTIONS
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
HUMAN = ROOT / "examples/v2/bounded-pilot-attachment-mutool-human-approval.approved.json"
HUMAN_SCHEMA = ROOT / "schemas/json/bounded-pilot-attachment-mutool-human-approval.schema.json"
AUTH = ROOT / "examples/v2/bounded-pilot-attachment-mutool-execution-authorization.approved.json"
AUTH_SCHEMA = (
    ROOT / "schemas/json/bounded-pilot-attachment-mutool-execution-authorization.schema.json"
)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_exact_mutool_human_approval_is_closed_and_bound() -> None:
    result = validate_json_schema(HUMAN, HUMAN_SCHEMA)
    assert not result.errors, result.errors
    approval = json.loads(HUMAN.read_text())
    assert sha256(approval["approval_statement"].encode()).hexdigest() == (
        "684111ba559e045fbec3223a4ce419a0c7aafb88d9bb189c7be0159faa4c6b2a"
    )
    assert approval["approved_request"]["sha256"] == _digest(
        ROOT / approval["approved_request"]["path"]
    )
    assert approval["prohibited_actions"] == PROHIBITED_ACTIONS
    assert "does not authorize stderr-content review or a retry" in approval["approval_statement"]


def test_final_mutool_authorization_is_closed_and_exactly_pinned() -> None:
    result = validate_json_schema(AUTH, AUTH_SCHEMA)
    assert not result.errors, result.errors
    authorization = json.loads(AUTH.read_text())
    for key in ("execution_request", "wrapper", "method", "method_approval", "human_approval"):
        pin = authorization[key]
        assert pin["sha256"] == _digest(ROOT / pin["path"])
    for key in (
        "authorization_effective",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "local_only",
    ):
        assert authorization[key] is True
    for key in (
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        assert authorization[key] is False
