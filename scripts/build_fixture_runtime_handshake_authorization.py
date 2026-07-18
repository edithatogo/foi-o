"""Build the exact approved, local-only fixture runtime-handshake authorization chain."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
REQUEST_SHA256 = "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"
PREPARATION_COMMIT = "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
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
APPROVAL_STATEMENT_SHA256 = "29cf6248c223719e6c403347d3dac4877a9cf701a3c0d4b99568ff0916bceca9"
RECORDED_AT = "2026-07-18T23:22:46+10:00"
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


def _write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _pin(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }


def main(output: Path = PACKET, *, repository_root: Path = ROOT) -> None:
    root = repository_root.resolve(strict=True)
    output.mkdir(parents=True, exist_ok=True)
    request_path = output / "role-authorization-request.pending.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if sha256(request_path.read_bytes()).hexdigest() != REQUEST_SHA256:
        raise ValueError("approved pending request SHA-256 mismatch")
    review_path = output / "role-authorization-approval.approved.json"
    _write(
        review_path,
        {
            "schema_version": "foi-o.fixture-role-authorization-approval.v0.1.0",
            "approval_id": "local-fixture-role-execution-2026-07-18",
            "status": "approved_bounded_local_runtime_handshake",
            "approved_by": "human:edithatogo",
            "approved_on": "2026-07-18",
            "recorded_at": RECORDED_AT,
            "recording_note": "recorded_at is repository provenance only and is not claimed as approval time",
            "approval_statement": APPROVAL_STATEMENT,
            "approval_statement_sha256": APPROVAL_STATEMENT_SHA256,
            "approved_request": _pin(request_path, root),
            "approved_repository_commit": PREPARATION_COMMIT,
            "scope": "bounded_local_fixture_runtime_handshake_only",
            "handshake_approved": True,
            "context_delivery_approved": False,
            "analyst_execution_approved": False,
            "final_execution_wrapper_required": True,
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
    wrapper_path = output / "runtime-handshake-authorization.approved.json"
    _write(
        wrapper_path,
        {
            "schema_version": "foi-o.fixture-runtime-handshake-authorization.v0.1.0",
            "authorization_id": "local-fixture-runtime-handshake-2026-07-18",
            "status": "approved_runtime_handshake_only",
            "approved_by": "human:edithatogo",
            "approved_on": "2026-07-18",
            "recorded_at": RECORDED_AT,
            "preparation_commit": PREPARATION_COMMIT,
            "request": _pin(request_path, root),
            "approval_review": _pin(review_path, root),
            "approved_input_readiness": request["approved_input_readiness"],
            "handshake_prompt": request["handshake_prompt"],
            "future_execution_prompts": request["future_execution_prompts"],
            "role_provenance": request["role_provenance"],
            "context_presentation": request["context_presentation"],
            "isolation_plan": request["isolation_plan"],
            "runtime_handshake_allowed": True,
            "context_presentation_allowed": False,
            "analysis_execution_allowed": False,
            "reconciliation_allowed": False,
            "final_execution_wrapper_required": True,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )


if __name__ == "__main__":
    main()
