"""Atomic staged runtime for bounded dual analysis and reconciliation.

This module never presents contexts. It accepts both isolated analyst returns
in one call, validates both completely in memory, then installs both sets and
their lock as one owner-only directory transaction. Reconciliation is a later,
separate transaction over verified disagreements only.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from foi_o_nz import bounded_pilot_execution as execution
from foi_o_nz.bounded_pilot_empirical_results import (
    ANALYST_IDS,
    RECONCILER_ID,
    build_analysis_set,
    build_dual_analysis_lock,
    build_reconciliation_set,
    canonical_sha256,
    compute_candidate_diagnostics,
    context_manifest_sha256,
    disagreement_ids,
    validate_dual_lock,
)
from foi_o_nz.bounded_pilot_execution import StagePermission

HANDSHAKE_READINESS_PATH = "examples/v2/bounded-pilot-runtime-handshake-readiness.locked.json"
HANDSHAKE_READINESS_SHA256 = "94587ec0abd150bcf68890dd047287dbe50a5a4023b5017b30d881da9f218918"
HANDSHAKE_READINESS_COMMIT = "dacb53a347139df9aa32b779d500329bacb7560e"
ANALYSIS_NAMES = ("analysis-set.analyst-a.locked.json", "analysis-set.analyst-b.locked.json")
LOCK_NAME = "dual-analysis-lock.locked.json"
RECONCILIATION_NAME = "reconciliation-set.locked.json"
DIAGNOSTICS_NAME = "candidate-diagnostics.locked.json"


@dataclass(frozen=True, slots=True)
class DualLockResult:
    """Metadata-only result of an atomic dual-analysis lock."""

    directory: Path
    analysis_sha256: tuple[str, str]
    lock_sha256: str
    disagreement_request_ids: tuple[str, ...]
    reconciliation_allowed: bool


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Metadata-only result of reconciliation and diagnostics."""

    directory: Path
    reconciliation_sha256: str
    diagnostics_sha256: str
    empirical_result_approved: bool
    publication_allowed: bool


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _strict_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _strict_load(path: Path) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError("runtime artifact must be a JSON object")
    return value


def _repo_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("unsafe runtime repository path")
    path = root.joinpath(*pure.parts)
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != root.parent):
        raise ValueError("runtime repository path contains a symlink")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("runtime repository path escapes root")
    return resolved


def _repo_file_at_head(permission: StagePermission, relative: str) -> Path:
    root = permission.repository_root
    if _git(root, "rev-parse", "HEAD") != permission.repository_commit:
        raise ValueError("runtime HEAD differs from authorization")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("runtime worktree is not clean")
    path = _repo_path(root, relative)
    committed = subprocess.run(
        ["git", "show", f"{permission.repository_commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    if committed != path.read_bytes():
        raise ValueError("runtime evidence differs from committed HEAD")
    return path


def _authorized_roles(permission: StagePermission) -> dict[str, dict[str, Any]]:
    auth = _strict_load(permission.authorization_path)
    plan = _strict_load(_repo_path(permission.repository_root, auth["plan"]["path"]))
    request = _strict_load(
        _repo_path(permission.repository_root, plan["governed_inputs"]["analyst_request"]["path"])
    )
    roles = request["roles"]
    if set(roles) != {"analyst_a", "analyst_b", "reconciler"}:
        raise ValueError("authorized role envelope set is not exact")
    return roles


def _runtime_envelope(permission: StagePermission, role_key: str) -> dict[str, Any]:
    readiness_path = _repo_file_at_head(permission, HANDSHAKE_READINESS_PATH)
    readiness_bytes = readiness_path.read_bytes()
    if sha256(readiness_bytes).hexdigest() != HANDSHAKE_READINESS_SHA256:
        raise ValueError("runtime handshake readiness digest mismatch")
    committed_readiness = subprocess.run(
        ["git", "show", f"{HANDSHAKE_READINESS_COMMIT}:{HANDSHAKE_READINESS_PATH}"],
        cwd=permission.repository_root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    if committed_readiness != readiness_bytes:
        raise ValueError("runtime handshake readiness differs from its exact commit")
    readiness = _strict_load(readiness_path)
    role = _authorized_roles(permission)[role_key]
    evidence_pin = next(
        (pin for pin in readiness["evidence"] if pin["actor_id"] == role["actor_id"]), None
    )
    if evidence_pin is None or set(evidence_pin) != {"actor_id", "path", "sha256"}:
        raise ValueError(f"{role_key} handshake pin is absent")
    path = _repo_file_at_head(permission, evidence_pin["path"])
    if sha256(path.read_bytes()).hexdigest() != evidence_pin["sha256"]:
        raise ValueError(f"{role_key} handshake evidence digest mismatch")
    evidence = _strict_load(path)
    required = {
        "schema_version",
        "status",
        "actor_id",
        "actor_class",
        "role",
        "provider",
        "model",
        "session_id",
        "role_prompt_sha256",
        "handshake_prompt",
        "reply_sha256",
        "context_received",
        "candidate_labels_received",
        "peer_outputs_received",
        "ready_for_future_exact_authorization",
        "local_only",
        "execution_authorized",
        "empirical_result_approved",
    }
    expected_role = "reconciler" if role_key == "reconciler" else "analyst"
    if (
        set(evidence) != required
        or evidence["schema_version"] != "foi-o.bounded-pilot-runtime-handshake-evidence.v0.2.0"
        or evidence["status"] != "locked_context_free_runtime_handshake"
        or evidence["actor_id"] != role["actor_id"]
        or evidence["actor_class"] != "automated_agent"
        or evidence["role"] != expected_role
        or evidence["session_id"] != role["canonical_locator"]
        or evidence["role_prompt_sha256"] != role["prompt"]["sha256"]
        or evidence["provider"] != "OpenAI"
        or not isinstance(evidence["model"], str)
        or not evidence["model"]
        or evidence["context_received"] is not False
        or evidence["candidate_labels_received"] is not False
        or evidence["peer_outputs_received"] is not False
        or evidence["ready_for_future_exact_authorization"] is not True
        or evidence["execution_authorized"] is not False
        or evidence["empirical_result_approved"] is not False
    ):
        raise ValueError(f"{role_key} runtime handshake is not exact")
    reply = {
        "actor_id": evidence["actor_id"],
        "actor_class": evidence["actor_class"],
        "role": evidence["role"],
        "provider": evidence["provider"],
        "model": evidence["model"],
        "session_id": evidence["session_id"],
        "role_prompt_sha256": evidence["role_prompt_sha256"],
        "handshake_prompt_sha256": evidence["handshake_prompt"]["sha256"],
        "context_received": evidence["context_received"],
        "candidate_labels_received": evidence["candidate_labels_received"],
        "peer_outputs_received": evidence["peer_outputs_received"],
        "ready_for_future_exact_authorization": evidence["ready_for_future_exact_authorization"],
    }
    reply_bytes = json.dumps(reply, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if sha256(reply_bytes).hexdigest() != evidence["reply_sha256"]:
        raise ValueError(f"{role_key} runtime handshake reply hash mismatch")
    runtime = {
        "provider": evidence["provider"],
        "model": evidence["model"],
        "prompt_sha256": evidence["role_prompt_sha256"],
        "session_id": evidence["session_id"],
    }
    return {
        "actor_id": evidence["actor_id"],
        "actor_class": "automated_agent",
        "role": expected_role,
        "runtime": runtime,
    }


def _context(
    permission: StagePermission, *, allowed_stage_directories: frozenset[str]
) -> tuple[dict[str, Any], dict[str, str]]:
    execution.verify_materialized_contexts(
        permission, allowed_stage_directories=allowed_stage_directories
    )
    path = permission.workspace / "context-manifest.locked.json"
    manifest = _strict_load(path)
    return manifest, {
        "path": "context-manifest.locked.json",
        "sha256": context_manifest_sha256(manifest),
    }


def _pins(permission: StagePermission) -> tuple[dict[str, str], dict[str, str]]:
    auth = {"path": execution.AUTHORIZATION_PATH, "sha256": permission.authorization_sha256}
    authorization = _strict_load(permission.authorization_path)
    plan = _strict_load(_repo_path(permission.repository_root, authorization["plan"]["path"]))
    codebook_pin = plan["governed_inputs"]["codebook"]
    return auth, {"path": codebook_pin["path"], "sha256": codebook_pin["sha256"]}


def _write_transaction(directory: Path, values: tuple[tuple[str, object], ...]) -> None:
    if directory.exists() or directory.is_symlink():
        raise ValueError("stage output directory already exists")
    parent = directory.parent
    with tempfile.TemporaryDirectory(prefix=f".{directory.name}-", dir=parent) as temporary:
        temp = Path(temporary)
        temp.chmod(0o700)
        for name, value in values:
            path = temp / name
            path.write_bytes(_strict_bytes(value))
            path.chmod(0o600)
        temp.replace(directory)
    info = directory.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("stage directory mode is not exactly 0700")


def lock_dual_analysis(
    permission: StagePermission,
    *,
    analyst_a_records: list[dict[str, Any]],
    analyst_b_records: list[dict[str, Any]],
) -> DualLockResult:
    """Validate both complete in-memory sets before atomically writing either."""
    if not isinstance(analyst_a_records, list) or not isinstance(analyst_b_records, list):
        raise ValueError("both analyst result sets must be present in memory")
    manifest, manifest_pin = _context(permission, allowed_stage_directories=frozenset())
    authorization, codebook = _pins(permission)
    envelopes = (
        _runtime_envelope(permission, "analyst_a"),
        _runtime_envelope(permission, "analyst_b"),
    )
    if envelopes[0]["runtime"]["session_id"] == envelopes[1]["runtime"]["session_id"]:
        raise ValueError("analyst runtime sessions are not distinct")
    records = (analyst_a_records, analyst_b_records)
    for values, envelope in zip(records, envelopes, strict=True):
        if any(record.get("analyst") != envelope for record in values):
            raise ValueError("analyst record runtime differs from committed handshake")
    sets = tuple(
        build_analysis_set(
            analyst_id=actor,
            records=values,
            authorization=authorization,
            codebook=codebook,
            context_manifest_pin=manifest_pin,
            context_manifest=manifest,
        )
        for actor, values in zip(ANALYST_IDS, records, strict=True)
    )
    paths = tuple(f"analysis/{name}" for name in ANALYSIS_NAMES)
    lock = build_dual_analysis_lock(
        analysis_a=sets[0], analysis_b=sets[1], paths=paths, context_manifest=manifest
    )
    directory = permission.workspace / "analysis"
    _write_transaction(
        directory,
        ((ANALYSIS_NAMES[0], sets[0]), (ANALYSIS_NAMES[1], sets[1]), (LOCK_NAME, lock)),
    )
    return DualLockResult(
        directory=directory,
        analysis_sha256=(canonical_sha256(sets[0]), canonical_sha256(sets[1])),
        lock_sha256=canonical_sha256(lock),
        disagreement_request_ids=tuple(disagreement_ids(sets[0], sets[1])),
        reconciliation_allowed=True,
    )


def _locked_analyses(
    permission: StagePermission,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest, _ = _context(permission, allowed_stage_directories=frozenset({"analysis"}))
    directory = permission.workspace / "analysis"
    if {path.name for path in directory.iterdir()} != {*ANALYSIS_NAMES, LOCK_NAME}:
        raise ValueError("analysis lock inventory is not exact")
    for path in directory.iterdir():
        info = path.stat(follow_symlinks=False)
        if path.is_symlink() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("analysis lock file is not owner-only regular data")
    a, b, lock = (
        _strict_load(directory / ANALYSIS_NAMES[0]),
        _strict_load(directory / ANALYSIS_NAMES[1]),
        _strict_load(directory / LOCK_NAME),
    )
    paths = tuple(f"analysis/{name}" for name in ANALYSIS_NAMES)
    validate_dual_lock(lock, analysis_a=a, analysis_b=b, paths=paths, context_manifest=manifest)
    return a, b, lock, manifest


def reconcile_and_diagnose(
    permission: StagePermission, *, reconciler_records: list[dict[str, Any]]
) -> ReconciliationResult:
    """Atomically install disagreement-only reconciliation and diagnostics."""
    a, b, lock, manifest = _locked_analyses(permission)
    expected_ids = disagreement_ids(a, b)
    if [record.get("request_id") for record in reconciler_records] != expected_ids:
        raise ValueError("reconciler records are not the exact disagreement-only set")
    reconciler = _runtime_envelope(permission, "reconciler")
    analyst_sessions = {
        a["analyst"]["runtime"]["session_id"],
        b["analyst"]["runtime"]["session_id"],
    }
    if reconciler["runtime"]["session_id"] in analyst_sessions:
        raise ValueError("reconciler runtime session is not distinct")
    if reconciler["actor_id"] != RECONCILER_ID or any(
        record.get("reconciler") != reconciler for record in reconciler_records
    ):
        raise ValueError("reconciler runtime differs from committed handshake")
    paths = tuple(f"analysis/{name}" for name in ANALYSIS_NAMES)
    lock_path = f"analysis/{LOCK_NAME}"
    reconciliation = build_reconciliation_set(
        records=reconciler_records,
        reconciler=reconciler,
        analysis_a=a,
        analysis_b=b,
        analysis_lock=lock,
        analysis_paths=paths,
        analysis_lock_path=lock_path,
        context_manifest=manifest,
    )
    diagnostics = compute_candidate_diagnostics(
        analysis_a=a,
        analysis_b=b,
        analysis_lock=lock,
        analysis_paths=paths,
        analysis_lock_path=lock_path,
        reconciliation=reconciliation,
        context_manifest=manifest,
    )
    if any(
        value.get(key) is not False
        for value in (reconciliation, diagnostics)
        for key in ("empirical_result_approved", "human_reviewed", "gold_eligible")
    ):
        raise ValueError("runtime output attempted claim authorization")
    directory = permission.workspace / "reconciliation"
    _write_transaction(
        directory,
        ((RECONCILIATION_NAME, reconciliation), (DIAGNOSTICS_NAME, diagnostics)),
    )
    return ReconciliationResult(
        directory=directory,
        reconciliation_sha256=canonical_sha256(reconciliation),
        diagnostics_sha256=canonical_sha256(diagnostics),
        empirical_result_approved=False,
        publication_allowed=False,
    )
