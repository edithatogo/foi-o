"""Build an inert v0.2 fixture execution-authorization candidate."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from subprocess import run

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
RECORDED_AT = "2026-07-19T10:31:49+10:00"
HANDSHAKE_EVIDENCE_COMMIT = "21c6db101e3afee4de96d8e2d924331eb76d9dbe"
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
SINGLE_PINS = {
    "approved_input_readiness": (
        "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
        "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e",
    ),
    "protocol": (
        "docs/42-v2-analyst-execution-protocol.md",
        "ac3785bd823d43a43c7830e34f4f3b380472f271e21f19446cbc575f4b49eca0",
    ),
    "role_authorization_request": (
        "examples/v2/analyst-fixture-packet/role-authorization-request.pending.json",
        "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c",
    ),
    "role_authorization_approval": (
        "examples/v2/analyst-fixture-packet/role-authorization-approval.approved.json",
        "9290ac2d3934ff844cf98b1e5c39b42aa960b7f086279dc9bd652767252312b4",
    ),
    "runtime_handshake_authorization": (
        "examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json",
        "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f",
    ),
    "runtime_handshake_readiness": (
        "examples/v2/analyst-fixture-packet/runtime-handshake-readiness.locked.json",
        "709625146544dd0abad8af22acb718e7c68cabf0f41ac59cb310e30107e3cb6b",
    ),
    "handshake_prompt": (
        "examples/v2/analyst-fixture-packet/prompts/runtime-provenance-handshake.v1.txt",
        "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77",
    ),
    "context_presentation": (
        "examples/v2/analyst-fixture-packet/context-presentation.pending.json",
        "72b75eb688541a712a62bea2569fb84353930c089ebaf8fc1082128aa3ef0e63",
    ),
    "isolation_plan": (
        "examples/v2/analyst-fixture-packet/role-isolation-plan.pending.json",
        "fe2558b57c6a44b20fcde235c79ccc2a7517f6f774450a2f01e176a19cee18b9",
    ),
}
ROLES = {
    "orchestrator": {
        "future_prompt": "c817ee25c74ea08ebdecf28ad52d126bbc6e8debfd3a9d32f7c8f02c3571112a",
        "role_provenance": "b08dedc5f0c2f48f106f92aab5185d7decddea9a8995c5744ac8371ad68dc9c8",
        "runtime_evidence": "5fd5a148c76344021679aa478d74d2d88334bff2cc5c78508649abbe46bbce8b",
    },
    "analyst_a": {
        "future_prompt": "ab8cd28ea7b98eae235069555ef5d239ef47d6b8ca1fe1ee6715e67d0f045908",
        "role_provenance": "899bfc9a6a70fa916b5d65e21aa3b64cf31b02bc82ab319c94555a722c0b0b35",
        "runtime_evidence": "f61a108759139dd4cefa1179936cc4f8cbacf13380b588bd8f81f1f89cbd72ed",
    },
    "analyst_b": {
        "future_prompt": "3bcb3b37c8d3a19e51a152c0b72aee82dba088bf822aa8cdc299cbbf029dfb6a",
        "role_provenance": "9be881edce63ef461e91d7bc785fdf9fe23a97cbe3bee12ec35de98374bec208",
        "runtime_evidence": "b8012b39cf099015ad226c76814c4c2a96868e25345d113e20fa664f4062d024",
    },
    "reconciler": {
        "future_prompt": "80770f3b4335b7fb5b092a96265e41cef29f0c26081ae46afc9949b220661081",
        "role_provenance": "5df3c98f2c3535ddbfc3df0abb42fd668fa3a40b35982494c9fbc6cd20c990f7",
        "runtime_evidence": "e293e4eb036890b32d246bb4b123dae4f72636cb305da1fcf6a4982051e1671a",
    },
}


def _pin(root: Path, relative: str, expected_sha256: str) -> dict[str, str]:
    path = root / relative
    actual = sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"{relative}: SHA-256 mismatch")
    return {"path": relative, "sha256": actual}


def _role_pin(root: Path, role: str, kind: str, expected: str) -> dict[str, str]:
    if kind == "future_prompt":
        relative = f"examples/v2/analyst-fixture-packet/prompts/{role}.future-execution.v1.txt"
    elif kind == "role_provenance":
        relative = f"examples/v2/analyst-fixture-packet/role-provenance.{role}.pending.json"
    else:
        relative = f"examples/v2/analyst-fixture-packet/runtime-handshake-evidence.{role}.json"
    return _pin(root, relative, expected)


def main(output: Path = PACKET, *, repository_root: Path = ROOT) -> None:
    root = repository_root.resolve(strict=True)
    readiness_relative, readiness_sha = SINGLE_PINS["runtime_handshake_readiness"]
    committed_readiness = run(
        ["git", "show", f"{HANDSHAKE_EVIDENCE_COMMIT}:{readiness_relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    if sha256(committed_readiness).hexdigest() != readiness_sha:
        raise ValueError("locked runtime-handshake readiness commit mismatch")
    output.mkdir(parents=True, exist_ok=True)
    single_pins = {
        name: _pin(root, relative, digest) for name, (relative, digest) in SINGLE_PINS.items()
    }
    role_pins = {
        kind: {role: _role_pin(root, role, kind, values[kind]) for role, values in ROLES.items()}
        for kind in ("future_prompt", "role_provenance", "runtime_evidence")
    }
    candidate = {
        "schema_version": "foi-o.fixture-execution-authorization-candidate.v0.2.0",
        "candidate_id": "local-fixture-execution-authorization-candidate-2026-07-19",
        "status": "pending_exact_human_approval",
        "recorded_at": RECORDED_AT,
        "handshake_evidence_commit": HANDSHAKE_EVIDENCE_COMMIT,
        **single_pins,
        "future_execution_prompts": role_pins["future_prompt"],
        "role_provenance": role_pins["role_provenance"],
        "runtime_evidence": role_pins["runtime_evidence"],
        "human_approval_present": False,
        "approved_by": None,
        "approved_at": None,
        "authorization_effective": False,
        "pre_execution_verification_passed": False,
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
    (output / "execution-authorization-candidate.v0.2.pending.json").write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
