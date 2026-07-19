"""Build the approved executable fixture authorization in a fail-closed state."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from subprocess import run

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
RECORDED_AT = "2026-07-19T12:17:16+10:00"
CANDIDATE_COMMIT = "5cbfbe80beee96c67cdcabbf352b97d5dffd6cbf"
CANDIDATE_SHA256 = "a1aab22f6f7870497f639e871cc4aa13d209ca35b72f8da89559bcf9940dab1d"
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
APPROVAL_STATEMENT_SHA256 = "9fd8171b3bffa16b18015287a6c585b8b309cfe1ea8127946ff09780551dfef4"
PROHIBITED = [
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
]
INHERITED_KEYS = (
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
)


def _write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _pin(relative: str, physical: Path) -> dict[str, str]:
    return {"path": relative, "sha256": sha256(physical.read_bytes()).hexdigest()}


def main(output: Path = PACKET, *, repository_root: Path = ROOT) -> None:
    root = repository_root.resolve(strict=True)
    candidate_relative = (
        "examples/v2/analyst-fixture-packet/execution-authorization-candidate.v0.2.pending.json"
    )
    candidate_path = root / candidate_relative
    if sha256(candidate_path.read_bytes()).hexdigest() != CANDIDATE_SHA256:
        raise ValueError("approved inert candidate SHA-256 mismatch")
    committed_candidate = run(
        ["git", "show", f"{CANDIDATE_COMMIT}:{candidate_relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    if sha256(committed_candidate).hexdigest() != CANDIDATE_SHA256:
        raise ValueError("approved inert candidate commit mismatch")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    approval_name = "execution-authorization-candidate-approval.approved.json"
    approval_path = output / approval_name
    _write(
        approval_path,
        {
            "schema_version": "foi-o.fixture-execution-authorization-candidate-approval.v0.1.0",
            "approval_id": "local-fixture-executable-derivation-2026-07-19",
            "status": "approved_bounded_local_executable_derivation",
            "approved_by": "human:edithatogo",
            "approved_on": "2026-07-19",
            "recorded_at": RECORDED_AT,
            "recording_note": "recorded_at is repository provenance and is not claimed as approval time",
            "approval_statement": APPROVAL_STATEMENT,
            "approval_statement_sha256": APPROVAL_STATEMENT_SHA256,
            "approved_candidate": {
                "path": candidate_relative,
                "sha256": CANDIDATE_SHA256,
                "repository_commit": CANDIDATE_COMMIT,
            },
            "scope": "derive_bounded_local_fixture_executable_v0.2_only",
            "derivation_approved": True,
            "context_presentation_approved": False,
            "analysis_execution_approved": False,
            "committed_executable_required": True,
            "pre_execution_verification_required": True,
            "execution_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )
    executable = {
        "schema_version": "foi-o.fixture-execution-authorization.v0.2.0",
        "authorization_id": "local-fixture-executable-v0.2-2026-07-19",
        "status": "approved_pending_pre_execution_verification",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-19",
        "recorded_at": RECORDED_AT,
        "derived_from_candidate": {
            "path": candidate_relative,
            "sha256": CANDIDATE_SHA256,
            "repository_commit": CANDIDATE_COMMIT,
        },
        "candidate_approval": _pin(
            f"examples/v2/analyst-fixture-packet/{approval_name}", approval_path
        ),
        **{key: candidate[key] for key in INHERITED_KEYS},
        "role_execution_conditions": {
            "orchestrator": {
                "actor_id": "agent:orchestrator-fixture-stream",
                "may_coordinate": True,
                "may_label": False,
                "condition": "after_exact_pre_execution_verification",
            },
            "analyst_a": {
                "actor_id": "agent:analyst-fixture-a",
                "may_coordinate": False,
                "may_label": True,
                "condition": "after_exact_pre_execution_verification",
            },
            "analyst_b": {
                "actor_id": "agent:analyst-fixture-b",
                "may_coordinate": False,
                "may_label": True,
                "condition": "after_exact_pre_execution_verification",
            },
            "reconciler": {
                "actor_id": "agent:reconciler-fixture",
                "may_coordinate": False,
                "may_label": False,
                "condition": "after_exact_pre_execution_verification_and_both_analyst_result_sets_locked",
            },
        },
        "execution_authorization_present": True,
        "authorization_effective": False,
        "pre_execution_verification_required": True,
        "pre_execution_verification_passed": False,
        "context_presentation_authorized_conditionally": True,
        "analysis_execution_authorized_conditionally": True,
        "reconciliation_authorized_conditionally": True,
        "execution_authorized_conditionally": True,
        "context_presentation_allowed": False,
        "analysis_execution_allowed": False,
        "reconciliation_allowed": False,
        "execution_allowed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": PROHIBITED,
    }
    _write(output / "execution-authorization.v0.2.pending-verification.json", executable)


if __name__ == "__main__":
    main()
