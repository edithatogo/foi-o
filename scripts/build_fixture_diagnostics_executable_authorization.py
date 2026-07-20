"""Derive and verify the bounded local fixture-diagnostics authorization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

from jsonschema import Draft202012Validator

try:
    from scripts.build_fixture_diagnostics_method_candidate import verify as verify_candidate
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from build_fixture_diagnostics_method_candidate import verify as verify_candidate

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
CANDIDATE_PATH = "examples/v2/analyst-fixture-packet/diagnostics-method-candidate.pending.json"
CANDIDATE_SHA256 = "6e44b634e1bfde2cc21dd99f79fd0ad4bcd5a7fb96d361be7aae09567ed4c699"
CANDIDATE_COMMIT = "c104a4cf193ef5f26de66b584e6a8cf37864a97e"
RECORDED_AT = "2026-07-19T04:34:13Z"
APPROVAL_STATEMENT = (
    "I, edithatogo, approve pending fixture diagnostics-method candidate SHA-256 "
    "6e44b634e1bfde2cc21dd99f79fd0ad4bcd5a7fb96d361be7aae09567ed4c699 as committed in "
    "c104a4cf193ef5f26de66b584e6a8cf37864a97e for bounded local inter-agent diagnostics "
    "execution and finalization under the exact method recorded by that candidate. This approval "
    "does not authorize empirical-evidence claims, human-reviewed claims, gold promotion, legal "
    "certification, redistribution, publication, training, fine-tuning, release, dataset "
    "publication, or paper updates."
)
APPROVAL_STATEMENT_SHA256 = "4ae892642f0b03e291a8e0c80c5c2bae12fea17908b02cde16fa340ad94e188b"
APPROVAL_RELATIVE = "examples/v2/analyst-fixture-packet/diagnostics-method-approval.approved.json"
AUTHORIZATION_RELATIVE = "examples/v2/analyst-fixture-packet/diagnostics-execution-authorization.pending-verification.json"
ENDURING_PROHIBITIONS = [
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


@dataclass(frozen=True)
class DiagnosticsAuthorizationVerificationResult:
    """Permissions emitted only after exact committed-byte verification."""

    authorization_sha256: str
    repository_commit: str
    bootstrap_execution_allowed: bool = True
    diagnostics_finalization_allowed: bool = True


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _strict_load(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite {token}")),
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: object required")
    return value


def _canonical(root: Path, relative: str) -> Path:
    path = root / relative
    if path.is_symlink() or path.resolve(strict=True) != path.absolute():
        raise ValueError(f"{relative}: path is not canonical")
    return path


def _committed(root: Path, commit: str, relative: str) -> bytes:
    result = run(
        ["git", "show", f"{commit}:{relative}"], cwd=root, check=False, capture_output=True
    )
    if result.returncode != 0:
        raise ValueError(f"{relative}: missing committed bytes")
    return result.stdout


def _candidate_pin() -> dict[str, str]:
    return {
        "path": CANDIDATE_PATH,
        "sha256": CANDIDATE_SHA256,
        "repository_commit": CANDIDATE_COMMIT,
    }


def _approval() -> dict[str, Any]:
    return {
        "schema_version": "foi-o.fixture-diagnostics-method-approval.v0.1.0",
        "approval_id": "local-fixture-diagnostics-method-2026-07-19",
        "status": "approved_bounded_local_diagnostics_derivation",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-19",
        "recorded_at": RECORDED_AT,
        "recording_note": "recorded_at is repository provenance and is not claimed as approval time",
        "approval_statement": APPROVAL_STATEMENT,
        "approval_statement_sha256": APPROVAL_STATEMENT_SHA256,
        "approved_candidate": _candidate_pin(),
        "scope": "derive_bounded_local_fixture_diagnostics_authorization_only",
        "derivation_approved": True,
        "committed_authorization_required": True,
        "pre_execution_verification_required": True,
        "bootstrap_execution_allowed": False,
        "diagnostics_finalization_allowed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": ENDURING_PROHIBITIONS,
    }


def _authorization(approval_digest: str) -> dict[str, Any]:
    return {
        "schema_version": "foi-o.fixture-diagnostics-execution-authorization.v0.1.0",
        "authorization_id": "local-fixture-diagnostics-executable-2026-07-19",
        "status": "approved_pending_pre_execution_verification",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-19",
        "recorded_at": RECORDED_AT,
        "method_candidate": _candidate_pin(),
        "method_approval": {"path": APPROVAL_RELATIVE, "sha256": approval_digest},
        "scope": "bounded_local_inter_agent_fixture_diagnostics_only",
        "authorization_effective": False,
        "pre_execution_verification_required": True,
        "pre_execution_verification_passed": False,
        "bootstrap_execution_authorized_conditionally": True,
        "diagnostics_finalization_authorized_conditionally": True,
        "bootstrap_execution_allowed": False,
        "diagnostics_results_present": False,
        "diagnostics_finalization_allowed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": ENDURING_PROHIBITIONS,
    }


def build(*, repository_root: Path, output_dir: Path = PACKET) -> tuple[Path, Path]:
    """Build inert approval and authorization artifacts from the exact approved candidate."""
    root = repository_root.resolve(strict=True)
    candidate = _canonical(root, CANDIDATE_PATH)
    if sha256(candidate.read_bytes()).hexdigest() != CANDIDATE_SHA256:
        raise ValueError("approved diagnostics candidate SHA-256 mismatch")
    if _committed(root, CANDIDATE_COMMIT, CANDIDATE_PATH) != candidate.read_bytes():
        raise ValueError("approved diagnostics candidate committed bytes mismatch")
    output_dir.mkdir(parents=True, exist_ok=True)
    approval_path = output_dir / Path(APPROVAL_RELATIVE).name
    authorization_path = output_dir / Path(AUTHORIZATION_RELATIVE).name
    _write(approval_path, _approval())
    _write(authorization_path, _authorization(sha256(approval_path.read_bytes()).hexdigest()))
    for artifact, schema_name in (
        (approval_path, "fixture-diagnostics-method-approval.schema.json"),
        (authorization_path, "fixture-diagnostics-execution-authorization.schema.json"),
    ):
        schema = _strict_load(_canonical(root, f"schemas/json/{schema_name}"))
        Draft202012Validator(schema).validate(_strict_load(artifact))
    return approval_path, authorization_path


def verify(
    *,
    repository_root: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    authorization_path: Path | None = None,
) -> DiagnosticsAuthorizationVerificationResult:
    """Verify the exact clean committed authorization DAG and emit bounded permission."""
    root = repository_root.resolve(strict=True)
    canonical_authorization = _canonical(root, AUTHORIZATION_RELATIVE)
    supplied_raw = authorization_path or canonical_authorization
    supplied_absolute = supplied_raw.absolute()
    if supplied_raw.is_symlink() or supplied_absolute != canonical_authorization:
        raise ValueError("diagnostics authorization path is not canonical")
    supplied = supplied_raw.resolve(strict=True)
    digest = sha256(supplied.read_bytes()).hexdigest()
    if digest != expected_authorization_sha256:
        raise ValueError("authorization SHA-256 mismatch")
    authorization = _strict_load(supplied)
    schema = _strict_load(
        _canonical(root, "schemas/json/fixture-diagnostics-execution-authorization.schema.json")
    )
    Draft202012Validator(schema).validate(authorization)
    approval_path = _canonical(root, APPROVAL_RELATIVE)
    approval = _strict_load(approval_path)
    approval_schema = _strict_load(
        _canonical(root, "schemas/json/fixture-diagnostics-method-approval.schema.json")
    )
    Draft202012Validator(approval_schema).validate(approval)
    if approval != _approval():
        raise ValueError("diagnostics method approval is not exact")
    approval_digest = sha256(approval_path.read_bytes()).hexdigest()
    if authorization != _authorization(approval_digest):
        raise ValueError("diagnostics execution authorization is not exact")
    if authorization["method_approval"] != {
        "path": APPROVAL_RELATIVE,
        "sha256": approval_digest,
    }:
        raise ValueError("diagnostics approval pin mismatch")
    head = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != expected_repository_commit:
        raise ValueError("repository HEAD does not match authorization commit")
    verify_candidate(
        repository_root=root,
        expected_sha256=CANDIDATE_SHA256,
        expected_commit=CANDIDATE_COMMIT,
    )
    if (
        _committed(root, expected_repository_commit, AUTHORIZATION_RELATIVE)
        != supplied.read_bytes()
    ):
        raise ValueError("authorization differs from anchored commit")
    if (
        _committed(root, expected_repository_commit, APPROVAL_RELATIVE)
        != approval_path.read_bytes()
    ):
        raise ValueError("approval differs from anchored commit")
    ancestry = run(
        ["git", "merge-base", "--is-ancestor", CANDIDATE_COMMIT, expected_repository_commit],
        cwd=root,
        check=False,
    )
    if ancestry.returncode != 0:
        raise ValueError("authorization commit does not descend from approved candidate commit")
    status = run(
        ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
    ).stdout
    if status:
        raise ValueError("repository worktree is not clean")
    return DiagnosticsAuthorizationVerificationResult(digest, expected_repository_commit)


if __name__ == "__main__":
    build(repository_root=ROOT)
