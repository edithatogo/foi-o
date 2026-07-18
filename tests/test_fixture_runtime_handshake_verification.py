import json
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

import pytest

from foi_o_nz.analyst_packet_verification import (
    verify_analyst_execution_packet,
    verify_fixture_runtime_handshake_authorization,
)
from scripts.build_fixture_runtime_handshake_authorization import main as build_authorization

ROOT = Path(__file__).parents[1]
PACKET_RELATIVE = Path("examples/v2/analyst-fixture-packet")
BASE_COMMIT = "948d392df7fbbf49ea9b33646a0bdbd845505811"
PROMOTION_COMMIT = "fe875ab254ff914b18143cfe08fee202b8b532b1"
PREPARATION_COMMIT = "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
REQUEST_SHA256 = "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"


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
    return run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _committed_authorization(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(root)], check=True)
    packet = root / PACKET_RELATIVE
    build_authorization(packet, repository_root=root)
    authorization = packet / "runtime-handshake-authorization.approved.json"
    commit = _commit(root, "runtime handshake authorization")
    return root, authorization, _digest(authorization), commit


def _verify(root: Path, authorization: Path, digest: str, commit: str) -> None:
    result = verify_fixture_runtime_handshake_authorization(
        repository_root=root,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        expected_request_sha256=REQUEST_SHA256,
        expected_preparation_repository_commit=PREPARATION_COMMIT,
        expected_base_repository_commit=BASE_COMMIT,
        expected_promotion_repository_commit=PROMOTION_COMMIT,
    )
    assert result.runtime_handshake_allowed is True
    assert result.context_presentation_allowed is False
    assert result.analysis_execution_allowed is False
    assert result.reconciliation_allowed is False
    assert result.role_count == 4


def test_public_verifier_accepts_exact_committed_handshake_only_gate(tmp_path: Path) -> None:
    root, authorization, digest, commit = _committed_authorization(tmp_path)
    _verify(root, authorization, digest, commit)


def test_public_verifier_rejects_incorrect_external_authorization_sha256(
    tmp_path: Path,
) -> None:
    root, authorization, _, commit = _committed_authorization(tmp_path)
    with pytest.raises(ValueError, match="runtime handshake authorization SHA-256 mismatch"):
        _verify(root, authorization, "0" * 64, commit)


def test_public_verifier_rejects_incorrect_external_repository_commit(
    tmp_path: Path,
) -> None:
    root, authorization, digest, _ = _committed_authorization(tmp_path)
    with pytest.raises(ValueError, match="fixture authorization commit ancestry mismatch"):
        _verify(root, authorization, digest, "0" * 40)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("analysis", "runtime_handshake_authorization"),
        ("context", "runtime_handshake_authorization"),
        ("reconciliation", "runtime_handshake_authorization"),
        ("handshake_disabled", "runtime_handshake_authorization"),
        ("final_wrapper_disabled", "runtime_handshake_authorization"),
        ("prohibition_reordered", "runtime handshake prohibitions are not exact"),
        ("prohibition_missing", "runtime_handshake_authorization.prohibited_actions"),
        ("prohibition_extra", "runtime_handshake_authorization.prohibited_actions"),
        ("inherited_pin", "approved_input_readiness: differs from the approved pending request"),
        ("preparation_commit", "runtime_handshake_authorization.preparation_commit"),
        ("request_pin", "runtime_handshake_authorization.request.sha256"),
        ("approval_text", "approval_review"),
        ("approval_pin", "approval_review: SHA-256 mismatch"),
        ("path_escape", "runtime_handshake_authorization.request.path"),
    ],
)
def test_public_verifier_rejects_rehashed_handshake_gate_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root, authorization, _, _ = _committed_authorization(tmp_path)
    document = _load(authorization)
    if mutation == "analysis":
        document["analysis_execution_allowed"] = True
    elif mutation == "context":
        document["context_presentation_allowed"] = True
    elif mutation == "reconciliation":
        document["reconciliation_allowed"] = True
    elif mutation == "handshake_disabled":
        document["runtime_handshake_allowed"] = False
    elif mutation == "final_wrapper_disabled":
        document["final_execution_wrapper_required"] = False
    elif mutation == "prohibition_reordered":
        document["prohibited_actions"][0], document["prohibited_actions"][1] = (  # type: ignore[index]
            document["prohibited_actions"][1],  # type: ignore[index]
            document["prohibited_actions"][0],  # type: ignore[index]
        )
    elif mutation == "prohibition_missing":
        document["prohibited_actions"].pop()  # type: ignore[union-attr]
    elif mutation == "prohibition_extra":
        document["prohibited_actions"].append("execution")  # type: ignore[union-attr]
    elif mutation == "inherited_pin":
        document["approved_input_readiness"]["sha256"] = "0" * 64  # type: ignore[index]
    elif mutation == "preparation_commit":
        document["preparation_commit"] = "0" * 40
    elif mutation == "request_pin":
        document["request"]["sha256"] = "0" * 64  # type: ignore[index]
    elif mutation == "approval_text":
        approval_path = root / document["approval_review"]["path"]  # type: ignore[index]
        approval = _load(approval_path)
        approval["approval_statement"] = "substituted approval"
        approval["approval_statement_sha256"] = sha256(b"substituted approval").hexdigest()
        _write(approval_path, approval)
        document["approval_review"]["sha256"] = _digest(approval_path)  # type: ignore[index]
    elif mutation == "approval_pin":
        document["approval_review"]["sha256"] = "0" * 64  # type: ignore[index]
    else:
        document["request"]["path"] = "../role-authorization-request.pending.json"  # type: ignore[index]
    _write(authorization, document)
    commit = _commit(root, f"mutation {mutation}")
    with pytest.raises(ValueError, match=message):
        _verify(root, authorization, _digest(authorization), commit)


def test_public_verifier_rejects_dirty_approved_review(tmp_path: Path) -> None:
    root, authorization, digest, commit = _committed_authorization(tmp_path)
    document = _load(authorization)
    approval_path = root / document["approval_review"]["path"]  # type: ignore[index]
    approval_path.write_bytes(approval_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="approval_review: SHA-256 mismatch"):
        _verify(root, authorization, digest, commit)


def test_public_verifier_rejects_dirty_authorization(tmp_path: Path) -> None:
    root, authorization, _, commit = _committed_authorization(tmp_path)
    document = _load(authorization)
    _write(authorization, document)
    authorization.write_bytes(authorization.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differs from anchored commit"):
        _verify(root, authorization, _digest(authorization), commit)


def test_public_verifier_rejects_untracked_authorization(tmp_path: Path) -> None:
    root, authorization, _, commit = _committed_authorization(tmp_path)
    untracked = root / "untracked-runtime-handshake-authorization.json"
    untracked.write_bytes(authorization.read_bytes())
    with pytest.raises(ValueError, match="not tracked at anchored commit"):
        _verify(root, untracked, _digest(untracked), commit)


def test_handshake_gate_is_explicitly_rejected_by_analysis_verifier(tmp_path: Path) -> None:
    root, authorization, digest, commit = _committed_authorization(tmp_path)
    with pytest.raises(ValueError, match="runtime handshake authorization cannot be used"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=authorization,
            expected_authorization_sha256=digest,
            expected_repository_commit=commit,
        )
