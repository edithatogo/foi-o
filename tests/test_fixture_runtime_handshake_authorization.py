import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_runtime_handshake_authorization import (
    main as build_authorization,
)

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
APPROVAL_STATEMENT = (
    "I, edithatogo, approve pending fixture role-authorization request SHA-256 "
    "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c as "
    "committed in 91013a0f69d3a376ec749bbad83902e7ac4dd2a7 for the bounded local fixture "
    "analyst execution described by that exact request. This approval authorizes creation of the "
    "final execution wrapper and subsequent execution only after that wrapper is committed and the "
    "pre-execution verifier passes against its exact SHA-256 and commit. Redistribution, publication, "
    "training, fine-tuning, release, dataset publication, gold promotion, legal certification, paper "
    "updates, human-reviewed claims, and empirical-evidence claims remain prohibited."
)
PROHIBITED_ACTIONS = {
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


def _load(name: str) -> dict[str, Any]:
    return json.loads((PACKET / name).read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_approval_review_preserves_verbatim_bounded_approval() -> None:
    name = "role-authorization-approval.approved.json"
    assert not validate_json_schema(
        PACKET / name, ROOT / "schemas/json/fixture-role-authorization-approval.schema.json"
    ).errors
    review = _load(name)
    assert review["approval_statement"] == APPROVAL_STATEMENT
    assert (
        review["approval_statement_sha256"]
        == sha256(APPROVAL_STATEMENT.encode("utf-8")).hexdigest()
    )
    assert review["approval_statement_sha256"] == (
        "29cf6248c223719e6c403347d3dac4877a9cf701a3c0d4b99568ff0916bceca9"
    )
    assert review["approved_on"] == "2026-07-18"
    assert (
        review["recording_note"]
        == "recorded_at is repository provenance only and is not claimed as approval time"
    )
    assert review["handshake_approved"] is True
    assert review["context_delivery_approved"] is False
    assert review["analyst_execution_approved"] is False
    assert review["final_execution_wrapper_required"] is True
    assert review["execution_allowed"] is False
    assert set(review["prohibited_actions"]) == PROHIBITED_ACTIONS


def test_runtime_handshake_wrapper_pins_complete_approved_chain() -> None:
    name = "runtime-handshake-authorization.approved.json"
    assert not validate_json_schema(
        PACKET / name,
        ROOT / "schemas/json/fixture-runtime-handshake-authorization.schema.json",
    ).errors
    wrapper = _load(name)
    request = _load("role-authorization-request.pending.json")
    assert (
        wrapper["request"]["sha256"]
        == "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"
    )
    assert wrapper["preparation_commit"] == "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
    for key in (
        "approved_input_readiness",
        "handshake_prompt",
        "future_execution_prompts",
        "role_provenance",
        "context_presentation",
        "isolation_plan",
    ):
        assert wrapper[key] == request[key]
    assert wrapper["approval_review"]["sha256"] == _digest(
        ROOT / wrapper["approval_review"]["path"]
    )
    for key in (
        "request",
        "approval_review",
        "approved_input_readiness",
        "handshake_prompt",
        "context_presentation",
        "isolation_plan",
    ):
        assert wrapper[key]["sha256"] == _digest(ROOT / wrapper[key]["path"])
    for group in ("future_execution_prompts", "role_provenance"):
        for pin in wrapper[group].values():
            assert pin["sha256"] == _digest(ROOT / pin["path"])
    assert wrapper["runtime_handshake_allowed"] is True
    assert wrapper["context_presentation_allowed"] is False
    assert wrapper["analysis_execution_allowed"] is False
    assert wrapper["reconciliation_allowed"] is False
    assert wrapper["final_execution_wrapper_required"] is True
    assert wrapper["empirical_evidence"] is False
    assert wrapper["human_reviewed"] is False
    assert wrapper["gold_eligible"] is False
    assert wrapper["release_qualifying"] is False
    assert wrapper["publication_eligible"] is False
    assert set(wrapper["prohibited_actions"]) == PROHIBITED_ACTIONS


def test_builder_is_byte_deterministic() -> None:
    before = {
        name: (PACKET / name).read_bytes()
        for name in (
            "role-authorization-approval.approved.json",
            "runtime-handshake-authorization.approved.json",
        )
    }
    build_authorization()
    assert before == {name: (PACKET / name).read_bytes() for name in before}
