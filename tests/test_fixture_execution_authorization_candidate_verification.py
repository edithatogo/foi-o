import json
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

import pytest

from foi_o_nz.analyst_packet_verification import (
    verify_analyst_execution_packet,
    verify_fixture_execution_authorization_candidate,
)
from scripts.build_fixture_execution_authorization_candidate import main as build_candidate

ROOT = Path(__file__).parents[1]
PACKET_RELATIVE = Path("examples/v2/analyst-fixture-packet")
BASE_COMMIT = "948d392df7fbbf49ea9b33646a0bdbd845505811"
PROMOTION_COMMIT = "fe875ab254ff914b18143cfe08fee202b8b532b1"
PREPARATION_COMMIT = "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
REQUEST_SHA256 = "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"
AUTHORIZATION_COMMIT = "393991ea0cfdaf9f016108bf74edae94b80f042a"
AUTHORIZATION_SHA256 = "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f"
EVIDENCE_COMMIT = "21c6db101e3afee4de96d8e2d924331eb76d9dbe"
EVIDENCE_SHA256 = "709625146544dd0abad8af22acb718e7c68cabf0f41ac59cb310e30107e3cb6b"


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _commit(root: Path, message: str) -> str:
    run(["git", "add", "."], cwd=root, check=True)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False)
    if staged.returncode == 1:
        run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                message,
            ],
            cwd=root,
            check=True,
        )
    elif staged.returncode != 0:
        staged.check_returncode()
    return run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _committed_candidate(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(root)], check=True)
    packet = root / PACKET_RELATIVE
    build_candidate(packet, repository_root=root)
    candidate = packet / "execution-authorization-candidate.v0.2.pending.json"
    commit = _commit(root, "prepare inert execution authorization candidate")
    return root, candidate, _digest(candidate), commit


def _verify(root: Path, candidate: Path, digest: str, commit: str) -> None:
    result = verify_fixture_execution_authorization_candidate(
        repository_root=root,
        candidate_path=candidate,
        expected_candidate_sha256=digest,
        expected_repository_commit=commit,
        expected_handshake_evidence_sha256=EVIDENCE_SHA256,
        expected_handshake_evidence_repository_commit=EVIDENCE_COMMIT,
        expected_authorization_sha256=AUTHORIZATION_SHA256,
        expected_authorization_repository_commit=AUTHORIZATION_COMMIT,
        expected_request_sha256=REQUEST_SHA256,
        expected_preparation_repository_commit=PREPARATION_COMMIT,
        expected_base_repository_commit=BASE_COMMIT,
        expected_promotion_repository_commit=PROMOTION_COMMIT,
    )
    assert result.role_count == 4
    assert result.human_approval_present is False
    assert result.authorization_effective is False
    assert result.execution_allowed is False


def test_public_verifier_accepts_exact_committed_inert_candidate(tmp_path: Path) -> None:
    root, candidate, digest, commit = _committed_candidate(tmp_path)
    _verify(root, candidate, digest, commit)


def test_public_verifier_rejects_incorrect_external_candidate_sha256(tmp_path: Path) -> None:
    root, candidate, _, commit = _committed_candidate(tmp_path)
    with pytest.raises(ValueError, match="candidate SHA-256 mismatch"):
        _verify(root, candidate, "0" * 64, commit)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("approval", "fixture_execution_authorization_candidate"),
        ("authorization_effective", "fixture_execution_authorization_candidate"),
        ("context", "fixture_execution_authorization_candidate"),
        ("analysis", "fixture_execution_authorization_candidate"),
        ("reconciliation", "fixture_execution_authorization_candidate"),
        ("execution", "fixture_execution_authorization_candidate"),
        ("prohibition_order", "prohibitions are not exact"),
        ("evidence_commit", "fixture_execution_authorization_candidate"),
        ("single_pin", "approved_input_readiness pin mismatch"),
        ("role_pin", "runtime_evidence.analyst_a pin mismatch"),
        ("missing_role", "fixture_execution_authorization_candidate.runtime_evidence"),
    ],
)
def test_public_verifier_rejects_rehashed_candidate_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root, candidate_path, _, _ = _committed_candidate(tmp_path)
    candidate = _load(candidate_path)
    if mutation == "approval":
        candidate["human_approval_present"] = True
    elif mutation == "authorization_effective":
        candidate["authorization_effective"] = True
    elif mutation == "context":
        candidate["context_presentation_allowed"] = True
    elif mutation == "analysis":
        candidate["analysis_execution_allowed"] = True
    elif mutation == "reconciliation":
        candidate["reconciliation_allowed"] = True
    elif mutation == "execution":
        candidate["execution_allowed"] = True
    elif mutation == "prohibition_order":
        candidate["prohibited_actions"][0], candidate["prohibited_actions"][1] = (
            candidate["prohibited_actions"][1],
            candidate["prohibited_actions"][0],
        )
    elif mutation == "evidence_commit":
        candidate["handshake_evidence_commit"] = "0" * 40
    elif mutation == "single_pin":
        candidate["approved_input_readiness"]["sha256"] = "0" * 64
    elif mutation == "role_pin":
        candidate["runtime_evidence"]["analyst_a"] = candidate["runtime_evidence"]["analyst_b"]
    else:
        candidate["runtime_evidence"].pop("reconciler")
    _write(candidate_path, candidate)
    commit = _commit(root, f"mutation {mutation}")
    with pytest.raises(ValueError, match=message):
        _verify(root, candidate_path, _digest(candidate_path), commit)


def test_public_verifier_rejects_relocated_dirty_and_untracked_candidate(
    tmp_path: Path,
) -> None:
    root, candidate, _, commit = _committed_candidate(tmp_path)
    relocated = root / "relocated-candidate.json"
    relocated.write_bytes(candidate.read_bytes())
    with pytest.raises(ValueError, match="candidate path is not canonical"):
        _verify(root, relocated, _digest(relocated), commit)

    candidate.write_bytes(candidate.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differs from anchored commit"):
        _verify(root, candidate, _digest(candidate), commit)


def test_inert_candidate_is_explicitly_rejected_by_analysis_verifier(tmp_path: Path) -> None:
    root, candidate, digest, commit = _committed_candidate(tmp_path)
    with pytest.raises(ValueError, match="candidate cannot be used for execution"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=candidate,
            expected_authorization_sha256=digest,
            expected_repository_commit=commit,
        )
