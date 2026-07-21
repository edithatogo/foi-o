import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_executable_authorization import main as build_executable

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
APPROVAL = PACKET / "execution-authorization-candidate-approval.approved.json"
EXECUTABLE = PACKET / "execution-authorization.v0.2.pending-verification.json"
APPROVAL_STATEMENT = (
    "I, edithatogo, approve pending fixture execution-authorization candidate SHA-256 "
    "a1aab22f6f7870497f639e871cc4aa13d209ca35b72f8da89559bcf9940dab1d as committed in "
    "5cbfbe80beee96c67cdcabbf352b97d5dffd6cbf for derivation of the bounded local executable "
    "v0.2 fixture authorization described by that exact candidate. This approval does not itself "
    "authorize context presentation or analysis; those remain prohibited until the separately "
    "derived executable authorization is committed and its pre-execution verifier passes against "
    "its exact SHA-256 and commit. Redistribution, publication, training, fine-tuning, release, "
    "dataset publication, gold promotion, legal certification, paper updates, human-reviewed claims, "
    "and empirical-evidence claims remain prohibited."
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_candidate_approval_preserves_exact_bounded_statement() -> None:
    assert not validate_json_schema(
        APPROVAL,
        ROOT / "schemas/json/fixture-execution-authorization-candidate-approval.schema.json",
    ).errors
    approval = _load(APPROVAL)
    assert approval["approval_statement"] == APPROVAL_STATEMENT
    assert (
        approval["approval_statement_sha256"]
        == sha256(APPROVAL_STATEMENT.encode("utf-8")).hexdigest()
    )
    assert approval["approval_statement_sha256"] == (
        "9fd8171b3bffa16b18015287a6c585b8b309cfe1ea8127946ff09780551dfef4"
    )
    assert approval["approved_on"] == "2026-07-19"
    assert approval["context_presentation_approved"] is False
    assert approval["analysis_execution_approved"] is False
    assert approval["execution_allowed"] is False


def test_executable_is_exact_candidate_derivative_pending_verification() -> None:
    assert not validate_json_schema(
        EXECUTABLE, ROOT / "schemas/json/fixture-execution-authorization.v0.2.schema.json"
    ).errors
    executable = _load(EXECUTABLE)
    candidate_path = ROOT / executable["derived_from_candidate"]["path"]
    candidate = _load(candidate_path)
    assert executable["derived_from_candidate"] == {
        "path": "examples/v2/analyst-fixture-packet/execution-authorization-candidate.v0.2.pending.json",
        "sha256": "a1aab22f6f7870497f639e871cc4aa13d209ca35b72f8da89559bcf9940dab1d",
        "repository_commit": "5cbfbe80beee96c67cdcabbf352b97d5dffd6cbf",
    }
    assert _digest(candidate_path) == executable["derived_from_candidate"]["sha256"]
    for key in (
        "handshake_evidence_commit",
        "approved_input_readiness",
        "protocol",
        "role_authorization_request",
        "role_authorization_approval",
        "runtime_handshake_authorization",
        "runtime_handshake_readiness",
        "handshake_prompt",
        "context_presentation",
        "isolation_plan",
        "future_execution_prompts",
        "role_provenance",
        "runtime_evidence",
    ):
        assert executable[key] == candidate[key]
    assert executable["candidate_approval"]["sha256"] == _digest(APPROVAL)
    assert executable["status"] == "approved_pending_pre_execution_verification"
    assert executable["execution_authorization_present"] is True
    assert executable["pre_execution_verification_required"] is True
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
        assert executable[key] is False


def test_conditional_role_scope_preserves_isolation_and_non_labeling_orchestration() -> None:
    executable = _load(EXECUTABLE)
    conditions = executable["role_execution_conditions"]
    assert set(conditions) == {"orchestrator", "analyst_a", "analyst_b", "reconciler"}
    assert conditions["orchestrator"] == {
        "actor_id": "agent:orchestrator-fixture-stream",
        "may_coordinate": True,
        "may_label": False,
        "condition": "after_exact_pre_execution_verification",
    }
    assert conditions["analyst_a"]["may_label"] is True
    assert conditions["analyst_b"]["may_label"] is True
    assert conditions["reconciler"] == {
        "actor_id": "agent:reconciler-fixture",
        "may_coordinate": False,
        "may_label": False,
        "condition": "after_exact_pre_execution_verification_and_both_analyst_result_sets_locked",
    }


def test_executable_builder_is_byte_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    build_executable(output, repository_root=ROOT)
    for path in (APPROVAL, EXECUTABLE):
        assert (output / path.name).read_bytes() == path.read_bytes()
