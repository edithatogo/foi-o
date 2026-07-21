import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_execution_authorization_candidate import main as build_candidate

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
CANDIDATE = PACKET / "execution-authorization-candidate.v0.2.pending.json"
SCHEMA = ROOT / "schemas/json/fixture-execution-authorization-candidate.v0.2.schema.json"
ROLES = {"orchestrator", "analyst_a", "analyst_b", "reconciler"}
PROHIBITED = {
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "gold_promotion",
    "legal_certification",
    "paper_update",
    "human_reviewed_claims",
    "empirical_evidence_claims",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_candidate_uses_distinct_strict_pending_schema() -> None:
    assert not validate_json_schema(CANDIDATE, SCHEMA).errors
    assert validate_json_schema(
        CANDIDATE, ROOT / "schemas/json/analyst-execution-authorization.v0.2.schema.json"
    ).errors
    candidate = _load(CANDIDATE)
    assert candidate["schema_version"] == ("foi-o.fixture-execution-authorization-candidate.v0.2.0")
    assert candidate["status"] == "pending_exact_human_approval"
    assert candidate["handshake_evidence_commit"] == ("21c6db101e3afee4de96d8e2d924331eb76d9dbe")
    assert candidate["runtime_handshake_readiness"]["sha256"] == (
        "709625146544dd0abad8af22acb718e7c68cabf0f41ac59cb310e30107e3cb6b"
    )


def test_candidate_pins_full_four_role_chain_and_remains_inert() -> None:
    candidate = _load(CANDIDATE)
    for key in (
        "approved_input_readiness",
        "protocol",
        "role_authorization_request",
        "role_authorization_approval",
        "runtime_handshake_authorization",
        "runtime_handshake_readiness",
        "handshake_prompt",
        "context_presentation",
        "isolation_plan",
    ):
        pin = candidate[key]
        assert pin["sha256"] == _digest(ROOT / pin["path"])
    for group in ("future_execution_prompts", "role_provenance", "runtime_evidence"):
        assert set(candidate[group]) == ROLES
        for role, pin in candidate[group].items():
            assert role in pin["path"]
            assert pin["sha256"] == _digest(ROOT / pin["path"])
    assert candidate["human_approval_present"] is False
    assert candidate["approved_by"] is None
    assert candidate["approved_at"] is None
    for key in (
        "authorization_effective",
        "pre_execution_verification_passed",
        "context_presentation_allowed",
        "analysis_execution_allowed",
        "reconciliation_allowed",
        "execution_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "release_qualifying",
        "publication_eligible",
    ):
        assert candidate[key] is False
    assert candidate["local_only"] is True
    assert set(candidate["prohibited_actions"]) == PROHIBITED


def test_candidate_builder_is_byte_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    build_candidate(output, repository_root=ROOT)
    generated = output / CANDIDATE.name
    assert generated.read_bytes() == CANDIDATE.read_bytes()
