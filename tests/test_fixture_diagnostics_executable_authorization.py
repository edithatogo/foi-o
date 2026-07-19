import json
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

import pytest

from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_diagnostics_executable_authorization import (
    APPROVAL_STATEMENT,
    build,
    verify,
)

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
APPROVAL = PACKET / "diagnostics-method-approval.approved.json"
AUTHORIZATION = PACKET / "diagnostics-execution-authorization.pending-verification.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_exact_approval_and_authorization_are_schema_valid_and_inert() -> None:
    assert not validate_json_schema(
        APPROVAL, ROOT / "schemas/json/fixture-diagnostics-method-approval.schema.json"
    ).errors
    assert not validate_json_schema(
        AUTHORIZATION,
        ROOT / "schemas/json/fixture-diagnostics-execution-authorization.schema.json",
    ).errors
    approval = _load(APPROVAL)
    authorization = _load(AUTHORIZATION)
    assert approval["approval_statement"] == APPROVAL_STATEMENT
    assert (
        approval["approval_statement_sha256"]
        == sha256(APPROVAL_STATEMENT.encode("utf-8")).hexdigest()
    )
    assert approval["approved_by"] == "human:edithatogo"
    assert approval["approved_on"] == "2026-07-19"
    assert approval["recorded_at"] != approval["approved_on"]
    assert authorization["method_approval"]["sha256"] == _digest(APPROVAL)
    for key in (
        "authorization_effective",
        "pre_execution_verification_passed",
        "bootstrap_execution_allowed",
        "diagnostics_finalization_allowed",
        "diagnostics_results_present",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "release_qualifying",
        "publication_eligible",
    ):
        assert authorization[key] is False


def test_builder_is_byte_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    build(repository_root=ROOT, output_dir=output)
    assert (output / APPROVAL.name).read_bytes() == APPROVAL.read_bytes()
    assert (output / AUTHORIZATION.name).read_bytes() == AUTHORIZATION.read_bytes()


def test_verifier_rejects_uncommitted_or_wrong_external_anchor() -> None:
    with pytest.raises(ValueError, match="authorization SHA-256 mismatch"):
        verify(
            repository_root=ROOT,
            expected_authorization_sha256="0" * 64,
            expected_repository_commit="0" * 40,
        )


def test_pending_candidate_cannot_be_used_as_executable() -> None:
    candidate = PACKET / "diagnostics-method-candidate.pending.json"
    with pytest.raises(ValueError, match="authorization path is not canonical"):
        verify(
            repository_root=ROOT,
            authorization_path=candidate,
            expected_authorization_sha256=_digest(candidate),
            expected_repository_commit="0" * 40,
        )


def test_verifier_rejects_alternate_and_symlink_paths(tmp_path: Path) -> None:
    alternate = tmp_path / AUTHORIZATION.name
    alternate.write_bytes(AUTHORIZATION.read_bytes())
    link = tmp_path / "authorization-link.json"
    link.symlink_to(AUTHORIZATION)
    for path in (alternate, link):
        with pytest.raises(ValueError, match="authorization path is not canonical"):
            verify(
                repository_root=ROOT,
                authorization_path=path,
                expected_authorization_sha256=_digest(AUTHORIZATION),
                expected_repository_commit="0" * 40,
            )


def test_verifier_requires_exact_head_commit_before_permission() -> None:
    with pytest.raises(ValueError, match="repository HEAD does not match authorization commit"):
        verify(
            repository_root=ROOT,
            expected_authorization_sha256=_digest(AUTHORIZATION),
            expected_repository_commit="0" * 40,
        )


def test_verifier_rejects_dirty_worktree_before_permission() -> None:
    head = run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    sentinel = ROOT / "diagnostics-verifier-dirty-sentinel.tmp"
    try:
        sentinel.write_text("intentional verifier test dirt\n", encoding="utf-8")
        status = run(
            ["git", "status", "--porcelain", "--", sentinel.name],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert sentinel.name in status
        with pytest.raises(ValueError, match="repository worktree is not clean"):
            verify(
                repository_root=ROOT,
                expected_authorization_sha256=_digest(AUTHORIZATION),
                expected_repository_commit=head,
            )
    finally:
        sentinel.unlink(missing_ok=True)
