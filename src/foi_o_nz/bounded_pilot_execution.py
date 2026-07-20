"""Fail-closed stage verifier and deterministic context builder for the pilot.

Import is inert. Restricted bytes are read only by ``materialize_contexts``
after an exact clean-HEAD authorization has minted a private capability.
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

PLAN_PATH = "examples/v2/bounded-pilot-batched-execution-plan.pending.json"
PLAN_SHA256 = "af7560655834373f97ca59c0a9876051325c855b8a73adc83110912ef0dc7782"
PLAN_COMMIT = "e9f53161d60eabaeeb5b5687ce57dca8bdcebe46"
APPROVAL_PATH = "examples/v2/bounded-pilot-batched-execution-approval.approved.json"
APPROVAL_SHA256 = "86da6f54b50c6251041cfa745ab402eeb2f2527b1065931a8101198dde0a01fb"
APPROVAL_COMMIT = "d9dc0a5f19ad39573ae5f45be409bbd3d07dde3a"
AUTHORIZATION_PATH = "examples/v2/bounded-pilot-batched-execution-authorization.approved.json"
REQUEST_35076_CONTEXT_SOURCE = Path("/private/tmp/fyi-content-snapshot-35076-approved")
SEPARATOR = "\n\n--- FOIO SEGMENT BOUNDARY ---\n\n"
_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class StagePermission:
    """Capability minted only by this module after exact verification."""

    authorization_sha256: str
    repository_commit: str
    repository_root: Path
    authorization_path: Path
    workspace: Path
    source_roots: dict[str, Path]
    evidence_manifest: dict[str, Any]
    derivation_result: dict[str, Any]
    unit_sha256_by_request: dict[str, str]
    stage: str
    reconciliation_allowed: bool

    def __init__(self, *, _token: object, **values: Any) -> None:
        """Reject construction outside this module."""
        if _token is not _TOKEN:
            raise ValueError("stage permission cannot be constructed directly")
        for name, value in values.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class ContextLock:
    """Metadata-only reference to atomically installed local contexts."""

    workspace: Path
    context_sha256: str
    manifest_sha256: str
    stage: str


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _strict_load(path: Path) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate JSON key in {path.name}: {key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value in {path.name}: {value}")

    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def _digest_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _digest(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _safe_repo_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("unsafe repository path")
    current = root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("repository path contains a symlink")
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("repository path escapes root")
    return resolved


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("pin does not contain a full commit")
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def _verify_pin(root: Path, pin: dict[str, Any], *, exact: dict[str, Any] | None = None) -> Path:
    allowed = ({"path", "sha256"}, {"path", "sha256", "repository_commit"})
    if set(pin) not in allowed or (exact is not None and pin != exact):
        raise ValueError("artifact pin is not exact")
    path = _safe_repo_path(root, pin["path"])
    data = path.read_bytes()
    if _digest_bytes(data) != pin["sha256"]:
        raise ValueError(f"artifact digest mismatch: {pin['path']}")
    if commit := pin.get("repository_commit"):
        if _git_blob(root, commit, pin["path"]) != data:
            raise ValueError(f"artifact differs from pinned commit: {pin['path']}")
    return path


def _reject_symlinks(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("local path contains a symlink")


def _private_dir(path: Path, *, exists: bool) -> Path:
    if not path.is_absolute():
        raise ValueError("local root is not absolute")
    _reject_symlinks(path if exists else path.parent)
    if exists:
        resolved = path.resolve(strict=True)
        info = resolved.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("local root is not an owner directory")
        if stat.S_IMODE(info.st_mode) & 0o022:
            raise ValueError("local root is group/world writable")
        return resolved
    if path.exists() or path.is_symlink():
        raise ValueError("workspace must be absent before S2")
    parent = path.parent.resolve(strict=True)
    info = parent.stat()
    private_tmp = parent == Path("/private/tmp") and bool(info.st_mode & stat.S_ISVTX)
    owner_private = info.st_uid == os.getuid() and not (stat.S_IMODE(info.st_mode) & 0o077)
    if not (private_tmp or owner_private):
        raise ValueError("workspace parent is not owner-only")
    return parent / path.name


def _descriptor_read(path: Path, *, expected_sha256: str, expected_bytes: int | None) -> bytes:
    _reject_symlinks(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
            raise ValueError("source is not an owner regular file")
        if stat.S_IMODE(before.st_mode) & 0o022:
            raise ValueError("source is group/world writable")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    observed = path.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ) or (after.st_dev, after.st_ino) != (observed.st_dev, observed.st_ino):
        raise ValueError("source changed during descriptor-safe read")
    data = b"".join(chunks)
    if (expected_bytes is not None and len(data) != expected_bytes) or _digest_bytes(
        data
    ) != expected_sha256:
        raise ValueError("source bytes differ from governed metadata")
    return data


def _authorization(
    root: Path, path: Path, expected_sha256: str, expected_commit: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if len(expected_sha256) != 64 or len(expected_commit) != 40:
        raise ValueError("external authorization anchor is not exact")
    if _git(root, "rev-parse", "HEAD") != expected_commit:
        raise ValueError("HEAD does not equal authorization commit")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("worktree is not clean")
    canonical = _safe_repo_path(root, AUTHORIZATION_PATH)
    if path.resolve(strict=True) != canonical or _digest(canonical) != expected_sha256:
        raise ValueError("authorization path or digest mismatch")
    if _git_blob(root, expected_commit, AUTHORIZATION_PATH) != canonical.read_bytes():
        raise ValueError("authorization differs from HEAD")
    auth = _strict_load(canonical)
    required = {
        "schema_version",
        "authorization_id",
        "status",
        "plan",
        "approval",
        "local_roots",
        "context_contract",
        "analyst_roles",
        "reconciler_role",
        "implementation_contracts",
        "runtime_handshake_readiness",
        "ordered_stages",
        "authorization_effective_after_verification",
        "context_materialization_authorized",
        "context_presentation_authorized",
        "analyst_execution_authorized",
        "reconciliation_authorized_conditionally",
        "candidate_manuscript_preparation_authorized",
        "local_package_validation_authorized",
        "final_exact_results_and_package_approval_required",
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "population_inference_allowed",
        "archive_wide_claim_allowed",
        "redistribution_allowed",
        "publication_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "paper_updates_allowed",
        "arxiv_submission_allowed",
        "external_action_allowed",
    }
    if set(auth) != required:
        raise ValueError("authorization keyset is not exact")
    if (
        auth["schema_version"] != "foi-o.bounded-pilot-batched-execution-authorization.v0.1.0"
        or auth["status"] != "approved_pending_exact_pre_execution_verification"
    ):
        raise ValueError("authorization state is not exact")
    true_flags = (
        "authorization_effective_after_verification",
        "context_materialization_authorized",
        "context_presentation_authorized",
        "analyst_execution_authorized",
        "reconciliation_authorized_conditionally",
        "candidate_manuscript_preparation_authorized",
        "local_package_validation_authorized",
        "final_exact_results_and_package_approval_required",
    )
    false_flags = (
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "population_inference_allowed",
        "archive_wide_claim_allowed",
        "redistribution_allowed",
        "publication_allowed",
        "release_allowed",
        "dataset_publication_allowed",
        "paper_updates_allowed",
        "arxiv_submission_allowed",
        "external_action_allowed",
    )
    if any(auth[key] is not True for key in true_flags) or any(
        auth[key] is not False for key in false_flags
    ):
        raise ValueError("authorization permissions are not exact")
    plan_exact = {"path": PLAN_PATH, "sha256": PLAN_SHA256, "repository_commit": PLAN_COMMIT}
    approval_exact = {
        "path": APPROVAL_PATH,
        "sha256": APPROVAL_SHA256,
        "repository_commit": APPROVAL_COMMIT,
    }
    plan = _strict_load(_verify_pin(root, auth["plan"], exact=plan_exact))
    approval = _strict_load(_verify_pin(root, auth["approval"], exact=approval_exact))
    if approval.get("approved_plan") != plan_exact:
        raise ValueError("approval does not bind exact plan")
    statement = approval.get("approval_statement")
    if not isinstance(statement, str) or approval.get("approval_statement_sha256") != _digest_bytes(
        statement.encode()
    ):
        raise ValueError("approval statement is not exact")
    approval_required = {
        "schema_version",
        "approved_by",
        "approved_on",
        "approval_statement",
        "approval_statement_sha256",
        "approved_plan",
        "local_stage_contract_creation_authorized",
        "conditional_local_execution_authorized_after_exact_verification",
        "final_exact_results_and_package_approval_required",
        "empirical_result_approved",
        "human_reviewed",
        "gold_eligible",
        "publication_allowed",
        "external_action_allowed",
    }
    if (
        set(approval) != approval_required
        or approval["schema_version"] != "foi-o.bounded-pilot-batched-execution-approval.v0.1.0"
        or approval["approved_by"] != "human:edithatogo"
    ):
        raise ValueError("approval semantics are not exact")
    if any(
        approval[key] is not False
        for key in (
            "empirical_result_approved",
            "human_reviewed",
            "gold_eligible",
            "publication_allowed",
            "external_action_allowed",
        )
    ):
        raise ValueError("approval contains prohibited permission")
    if any(
        approval[key] is not True
        for key in (
            "local_stage_contract_creation_authorized",
            "conditional_local_execution_authorized_after_exact_verification",
            "final_exact_results_and_package_approval_required",
        )
    ):
        raise ValueError("approval omits a required positive authorization")
    if (
        auth["local_roots"] != plan["local_roots"]
        or auth["context_contract"] != plan["context_contract"]
    ):
        raise ValueError("authorization differs from plan")
    for pin in plan["governed_inputs"].values():
        _verify_pin(root, pin)
    if (
        not isinstance(auth["implementation_contracts"], dict)
        or not auth["implementation_contracts"]
    ):
        raise ValueError("implementation contract pins are absent")
    for pin in auth["implementation_contracts"].values():
        _verify_pin(root, pin)
    _verify_pin(root, auth["runtime_handshake_readiness"])
    expected_stages = [f"S{index}" for index in range(2, 9)]
    if (
        not isinstance(auth["ordered_stages"], list)
        or [stage.get("id") for stage in auth["ordered_stages"]] != expected_stages
        or any(
            set(stage) != {"id", "authorized", "failure_action"}
            or stage["authorized"] is not True
            or stage["failure_action"] != "stop_fail_closed"
            for stage in auth["ordered_stages"]
        )
    ):
        raise ValueError("ordered stage authorization is not exact")
    request = _strict_load(
        _safe_repo_path(root, plan["governed_inputs"]["analyst_request"]["path"])
    )
    if auth["analyst_roles"] != {k: request["roles"][k] for k in ("analyst_a", "analyst_b")}:
        raise ValueError("analyst roles differ from request")
    if auth["reconciler_role"] != request["roles"]["reconciler"]:
        raise ValueError("reconciler role differs from request")
    return auth, plan


def _governed_metadata(
    root: Path, plan: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    approved = _strict_load(
        _safe_repo_path(root, plan["governed_inputs"]["approved_readiness"]["path"])
    )
    candidate = _strict_load(_verify_pin(root, approved["candidate"]))
    base = _strict_load(_verify_pin(root, candidate["derived_from_readiness"]))
    evidence = _strict_load(_verify_pin(root, base["artifacts"]["evidence_manifest"]))
    derivation = _strict_load(_verify_pin(root, candidate["attachment_derivation_result"]))
    if evidence.get("request_ids") != ["11872", "35076"] or [
        r["request_id"] for r in evidence["records"]
    ] != ["11872", "35076"]:
        raise ValueError("evidence census membership/order is not exact")
    if (
        evidence["records"][0]["correspondence"]["block_count"] != 4
        or evidence["records"][1]["correspondence"]["block_count"] != 1
    ):
        raise ValueError("correspondence census is not exact")
    attachments = evidence["records"][1]["attachments"]
    if not attachments["verified_empty"] or attachments["files"]:
        raise ValueError("request 35076 attachment inventory is not empty")
    if [(o["output_name"], o["source_sha256"]) for o in derivation["outputs"]] != [
        (f"attachment-{index:03d}.txt", item["sha256"])
        for index, item in enumerate(evidence["records"][0]["attachments"]["files"])
    ]:
        raise ValueError("derived attachment inventory differs from evidence census")
    units = {unit["request_id"]: unit["unit_sha256"] for unit in base["units"]}
    if list(units) != ["11872", "35076"]:
        raise ValueError("approved unit census is not exact")
    return evidence, derivation, units


def verify_pre_materialization(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
) -> StagePermission:
    """Mint the S2 capability from an exact clean-HEAD authorization."""
    root = repository_root.resolve(strict=True)
    auth, plan = _authorization(
        root, authorization_path, expected_authorization_sha256, expected_repository_commit
    )
    evidence, derivation, units = _governed_metadata(root, plan)
    roots = {
        key: _private_dir(Path(value), exists=True)
        for key, value in auth["local_roots"].items()
        if key != "execution_workspace"
    }
    request_35076_page = roots["request_35076_source"] / "content/page.html"
    if not request_35076_page.is_file():
        verification_path = roots["request_35076_source"] / "verification.json"
        verification = _strict_load(verification_path)
        record = evidence["records"][1]
        if (
            verification.get("source_manifest_sha256") != record["snapshot_manifest_sha256"]
            or verification.get("source_content_sha256") != record["page_html_sha256"]
            or verification.get("source_records_modified") is not False
            or verification.get("storage") != "local_only"
        ):
            raise ValueError("request 35076 provenance root does not bind the approved source")
        roots["request_35076_context_source"] = _private_dir(
            REQUEST_35076_CONTEXT_SOURCE, exists=True
        )
    workspace = _private_dir(Path(auth["local_roots"]["execution_workspace"]), exists=False)
    all_roots = [*roots.values(), workspace]
    if len(set(all_roots)) != len(all_roots) or any(
        a != b and (a.is_relative_to(b) or b.is_relative_to(a))
        for a in all_roots
        for b in all_roots
    ):
        raise ValueError("local roots overlap")
    return StagePermission(
        _token=_TOKEN,
        authorization_sha256=expected_authorization_sha256,
        repository_commit=expected_repository_commit,
        repository_root=root,
        authorization_path=authorization_path.resolve(strict=True),
        workspace=workspace,
        source_roots=roots,
        evidence_manifest=evidence,
        derivation_result=derivation,
        unit_sha256_by_request=units,
        stage="S2_CONTEXT_MATERIALIZATION",
        reconciliation_allowed=False,
    )


def _context_segments(permission: StagePermission) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    records = permission.evidence_manifest["records"]
    for record in records:
        request_id = record["request_id"]
        root_key = (
            "request_35076_context_source"
            if request_id == "35076" and "request_35076_context_source" in permission.source_roots
            else f"request_{request_id}_source"
        )
        page = permission.source_roots[root_key] / "content/page.html"
        page_data = _descriptor_read(
            page, expected_sha256=record["page_html_sha256"], expected_bytes=None
        )
        try:
            page_text = page_data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("page HTML is not strict UTF-8") from error
        for block in record["correspondence"]["blocks"]:
            start, end = block["text_span"]["start"], block["text_span"]["end"]
            text = page_text[start:end]
            if _digest_bytes(text.encode()) != block["text_sha256"]:
                raise ValueError("correspondence slice differs from governed census")
            result.append(
                {
                    "request_id": request_id,
                    "segment_id": block["element_id"],
                    "text": text,
                    "source_sha256": block["text_sha256"],
                    "source_kind": "correspondence",
                }
            )
        if request_id == "11872":
            for output in permission.derivation_result["outputs"]:
                path = permission.source_roots["derived_attachments"] / output["output_name"]
                data = _descriptor_read(
                    path,
                    expected_sha256=output["output_sha256"],
                    expected_bytes=output["byte_count"],
                )
                try:
                    text = data.decode("utf-8", errors="strict")
                except UnicodeDecodeError as error:
                    raise ValueError("derived attachment is not strict UTF-8") from error
                result.append(
                    {
                        "request_id": request_id,
                        "segment_id": output["output_name"],
                        "text": text,
                        "source_sha256": output["output_sha256"],
                        "source_kind": "attachment_derived_text",
                    }
                )
    return result


def _compose_context(
    permission: StagePermission,
) -> tuple[bytes, list[dict[str, Any]], list[dict[str, Any]]]:
    segments = _context_segments(permission)
    expected_ids = [
        block["element_id"]
        for record in permission.evidence_manifest["records"]
        for block in record["correspondence"]["blocks"]
    ]
    expected_ids[4:4] = [
        output["output_name"] for output in permission.derivation_result["outputs"]
    ]
    if [segment["segment_id"] for segment in segments] != expected_ids:
        raise ValueError("derived segment order is not exact")
    texts = [segment.pop("text") for segment in segments]
    context = SEPARATOR.join(texts)
    cursor = 0
    for index, (segment, text) in enumerate(zip(segments, texts, strict=True)):
        length = len(text)
        segment.update({"start": cursor, "end": cursor + length})
        cursor += length + (len(SEPARATOR) if index < len(segments) - 1 else 0)
    contexts: list[dict[str, Any]] = []
    global_cursor = 0
    for request_id in ("11872", "35076"):
        selected = [
            (segment, text)
            for segment, text in zip(segments, texts, strict=True)
            if segment["request_id"] == request_id
        ]
        unit_text = SEPARATOR.join(text for _, text in selected)
        unit_cursor = 0
        sources = []
        for index, (segment, text) in enumerate(selected):
            sources.append(
                {
                    "source_kind": segment["source_kind"],
                    "source_id": segment["segment_id"],
                    "source_sha256": segment["source_sha256"],
                    "start": unit_cursor,
                    "end": unit_cursor + len(text),
                    "character_count": len(text),
                }
            )
            unit_cursor += len(text) + (len(SEPARATOR) if index < len(selected) - 1 else 0)
        contexts.append(
            {
                "request_id": request_id,
                "unit_sha256": permission.unit_sha256_by_request[request_id],
                "context_sha256": _digest_bytes(unit_text.encode("utf-8")),
                "global_start": global_cursor,
                "global_end": global_cursor + len(unit_text),
                "sources": sources,
            }
        )
        global_cursor += len(unit_text) + (len(SEPARATOR) if request_id == "11872" else 0)
    return context.encode("utf-8"), segments, contexts


def materialize_contexts(permission: StagePermission) -> ContextLock:
    """Derive the exact census context and atomically install two copies plus lock."""
    if permission.stage != "S2_CONTEXT_MATERIALIZATION" or permission.reconciliation_allowed:
        raise ValueError("permission is not an S2 capability")
    refreshed = verify_pre_materialization(
        repository_root=permission.repository_root,
        authorization_path=permission.authorization_path,
        expected_authorization_sha256=permission.authorization_sha256,
        expected_repository_commit=permission.repository_commit,
    )
    if refreshed != permission:
        raise ValueError("permission changed during re-verification")
    encoded, segments, contexts = _compose_context(permission)
    context = encoded.decode("utf-8")
    digest = _digest_bytes(encoded)
    manifest = {
        "schema_version": "foi-o.bounded-pilot-context-manifest.v0.2.0",
        "status": "locked_local_contexts",
        "authorization_sha256": permission.authorization_sha256,
        "repository_commit": permission.repository_commit,
        "request_ids": ["11872", "35076"],
        "contexts": contexts,
        "analyst_context_sha256": digest,
        "byte_count": len(encoded),
        "codepoint_count": len(context),
        "segments": segments,
        "analyst_contexts_identical": True,
        "local_only": True,
        "reconciliation_allowed": False,
        "empirical_result_approved": False,
        "publication_allowed": False,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with tempfile.TemporaryDirectory(
        prefix=".foio-context-", dir=permission.workspace.parent
    ) as temp_name:
        temp = Path(temp_name)
        temp.chmod(0o700)
        for name, data in (
            ("analyst-a.context.txt", encoded),
            ("analyst-b.context.txt", encoded),
            ("context-manifest.locked.json", manifest_bytes),
        ):
            target = temp / name
            target.write_bytes(data)
            target.chmod(0o600)
        temp.replace(permission.workspace)
    return verify_materialized_contexts(permission)


def verify_materialized_contexts(
    permission: StagePermission,
    *,
    allowed_stage_directories: frozenset[str] = frozenset(),
) -> ContextLock:
    """Verify clean HEAD plus the exact installed context lock and mint S3 metadata."""
    if not allowed_stage_directories <= {"analysis", "reconciliation"}:
        raise ValueError("unknown stage directory allowance")
    _authorization(
        permission.repository_root,
        permission.authorization_path,
        permission.authorization_sha256,
        permission.repository_commit,
    )
    workspace = permission.workspace.resolve(strict=True)
    _reject_symlinks(workspace)
    workspace_info = workspace.stat()
    if workspace_info.st_uid != os.getuid() or stat.S_IMODE(workspace_info.st_mode) != 0o700:
        raise ValueError("context workspace mode is not exactly 0700")
    if {p.name for p in workspace.iterdir()} != {
        "analyst-a.context.txt",
        "analyst-b.context.txt",
        "context-manifest.locked.json",
        *allowed_stage_directories,
    }:
        raise ValueError("context workspace inventory is not exact")
    manifest_path = workspace / "context-manifest.locked.json"
    for path in (
        workspace / "analyst-a.context.txt",
        workspace / "analyst-b.context.txt",
        manifest_path,
    ):
        info = path.stat(follow_symlinks=False)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("installed context file mode is not exactly 0600")
    manifest = _strict_load(manifest_path)
    manifest_keys = {
        "schema_version",
        "status",
        "authorization_sha256",
        "repository_commit",
        "request_ids",
        "contexts",
        "analyst_context_sha256",
        "byte_count",
        "codepoint_count",
        "segments",
        "analyst_contexts_identical",
        "local_only",
        "reconciliation_allowed",
        "empirical_result_approved",
        "publication_allowed",
    }
    if (
        set(manifest) != manifest_keys
        or manifest.get("schema_version") != "foi-o.bounded-pilot-context-manifest.v0.2.0"
    ):
        raise ValueError("context manifest shape is not exact")
    paths = [workspace / "analyst-a.context.txt", workspace / "analyst-b.context.txt"]
    values = [
        _descriptor_read(
            path,
            expected_sha256=manifest["analyst_context_sha256"],
            expected_bytes=manifest["byte_count"],
        )
        for path in paths
    ]
    if values[0] != values[1]:
        raise ValueError("analyst contexts differ")
    expected_context, expected_segments, expected_contexts = _compose_context(permission)
    if (
        values[0] != expected_context
        or manifest.get("segments") != expected_segments
        or manifest.get("contexts") != expected_contexts
        or manifest.get("request_ids") != ["11872", "35076"]
    ):
        raise ValueError("context lock differs from governed metadata")
    if (
        manifest.get("authorization_sha256") != permission.authorization_sha256
        or manifest.get("repository_commit") != permission.repository_commit
        or manifest.get("analyst_contexts_identical") is not True
        or manifest.get("local_only") is not True
        or manifest.get("reconciliation_allowed") is not False
        or manifest.get("empirical_result_approved") is not False
        or manifest.get("publication_allowed") is not False
    ):
        raise ValueError("context lock does not bind exact execution")
    return ContextLock(
        workspace,
        manifest["analyst_context_sha256"],
        _digest(manifest_path),
        "S3_ANALYST_EXECUTION",
    )
