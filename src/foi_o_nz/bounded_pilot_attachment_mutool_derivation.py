"""Fail-closed MuPDF derivation for the bounded request-11872 pilot.

Importing this module is inert. Execution requires a permission minted from an
exact authorization committed at ``HEAD`` in a clean checkout.
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

AUTHORIZATION_RELATIVE_PATH = (
    "examples/v2/bounded-pilot-attachment-mutool-execution-authorization.approved.json"
)
REQUEST_RELATIVE_PATH = "examples/v2/bounded-pilot-attachment-mutool-execution-request.pending.json"
WRAPPER_RELATIVE_PATH = "src/foi_o_nz/bounded_pilot_attachment_mutool_derivation.py"
METHOD_RELATIVE_PATH = "examples/v2/bounded-pilot-attachment-alternative-text-method.pending.json"
METHOD_APPROVAL_RELATIVE_PATH = (
    "examples/v2/bounded-pilot-attachment-alternative-text-method-approval.approved.json"
)
HUMAN_APPROVAL_RELATIVE_PATH = (
    "examples/v2/bounded-pilot-attachment-mutool-human-approval.approved.json"
)
PROHIBITED_ACTIONS = [
    "context_presentation",
    "analyst_execution",
    "reconciliation",
    "empirical_claims",
    "population_inference",
    "archive_wide_claims",
    "human_reviewed_claims",
    "gold_promotion",
    "legal_certification",
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "paper_updates",
]
METHOD_APPROVAL_PROHIBITED_ACTIONS = [
    "pdf_processing",
    "derived_content_creation",
    "context_presentation",
    "analyst_execution",
    "reconciliation",
    "empirical_claims",
    "population_inference",
    "archive_wide_claims",
    "human_reviewed_claims",
    "gold_promotion",
    "legal_certification",
    "redistribution",
    "publication",
    "training_or_fine_tuning",
    "release_or_dataset_publication",
    "paper_updates",
]
_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class VerifiedMutoolPermission:
    """Capability minted only by the exact clean-HEAD verifier."""

    authorization_sha256: str
    repository_commit: str
    request_sha256: str
    source_root: Path
    output_directory: Path
    executable_path: Path
    executable_sha256: str

    def __init__(self, *, _token: object, **values: Any) -> None:
        """Reject all construction outside this module's verifier."""
        if _token is not _TOKEN:
            raise ValueError("MuPDF permission cannot be constructed directly")
        for name, value in values.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class MutoolDerivationResult:
    """Metadata and local path for a completed bounded derivation."""

    output_directory: Path
    manifest: dict[str, Any]


@dataclass(slots=True)
class _Frozen:
    source: dict[str, Any]
    original: Path
    descriptor: int
    device: int
    inode: int
    copy: Path


@dataclass(slots=True)
class _FrozenExecutable:
    original: Path
    descriptor: int
    device: int
    inode: int
    digest: str
    copy: Path


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _repo_file(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(p in {"", ".", ".."} for p in pure.parts):
        raise ValueError("unsafe repository path")
    current = root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("repository path contains a symlink")
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("repository artifact is not canonical")
    return resolved


def _tracked_repo_file(root: Path, relative: str) -> Path:
    path = _repo_file(root, relative)
    if _git(root, "ls-files", "--error-unmatch", relative) != relative:
        raise ValueError("governed artifact is not committed")
    return path


def _pin(root: Path, value: Any, expected_path: str) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("governed artifact pin is malformed")
    if value["path"] != expected_path:
        raise ValueError("governed artifact path is not exact")
    path = _tracked_repo_file(root, expected_path)
    if value["sha256"] != _digest(path):
        raise ValueError("governed artifact digest mismatch")
    return path


def verify_mutool_pre_execution(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    source_root: Path,
    output_directory: Path,
) -> VerifiedMutoolPermission:
    """Mint permission only from the future exact committed authorization."""
    root = repository_root.resolve(strict=True)
    canonical = _repo_file(root, AUTHORIZATION_RELATIVE_PATH)
    if (
        authorization_path.resolve(strict=True) != canonical
        or _digest(canonical) != expected_authorization_sha256
    ):
        raise ValueError("MuPDF authorization identity mismatch")
    if _git(root, "rev-parse", "HEAD") != expected_repository_commit:
        raise ValueError("MuPDF authorization commit is not HEAD")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("MuPDF repository is not clean")
    _tracked_repo_file(root, AUTHORIZATION_RELATIVE_PATH)
    auth = _object(canonical)
    expected = {
        "schema_version",
        "authorization_id",
        "status",
        "execution_request",
        "wrapper",
        "method",
        "method_approval",
        "human_approval",
        "source_root",
        "output_directory",
        "authorization_effective",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "local_only",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    }
    if (
        set(auth) != expected
        or auth["schema_version"]
        != "foi-o.bounded-pilot-attachment-mutool-execution-authorization.v0.1.0"
    ):
        raise ValueError("MuPDF authorization structure is not exact")
    if auth["status"] != "approved_exact_local_mutool_derivation" or not auth["authorization_id"]:
        raise ValueError("MuPDF authorization is not effective")
    for key in (
        "authorization_effective",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "local_only",
    ):
        if auth[key] is not True:
            raise ValueError("MuPDF authorization permission is absent")
    for key in (
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    ):
        if auth[key] is not False:
            raise ValueError("MuPDF authorization exceeds bounded scope")
    request_pin, wrapper_pin = auth["execution_request"], auth["wrapper"]
    request_path = _pin(root, request_pin, REQUEST_RELATIVE_PATH)
    wrapper_path = _pin(root, wrapper_pin, WRAPPER_RELATIVE_PATH)
    method_path = _pin(root, auth["method"], METHOD_RELATIVE_PATH)
    approval_path = _pin(root, auth["method_approval"], METHOD_APPROVAL_RELATIVE_PATH)
    human_path = _pin(root, auth["human_approval"], HUMAN_APPROVAL_RELATIVE_PATH)
    request = _object(request_path)
    request_keys = {
        "schema_version",
        "request_id",
        "status",
        "method",
        "method_approval",
        "wrapper",
        "wrapper_repository_commit",
        "source_root",
        "output_directory",
        "sources",
        "method_tool",
        "runtime_observation",
        "environment",
        "argv_template",
        "output_contract",
        "failure_contract",
        "requested_scope",
        "authorization_present",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    }
    if (
        set(request) != request_keys
        or request["schema_version"]
        != "foi-o.bounded-pilot-attachment-mutool-execution-request.v0.1.0"
        or request["status"] != "pending_exact_execution_authorization"
    ):
        raise ValueError("MuPDF request structure is not exact")
    if (
        request["request_id"] != "bounded-pilot-11872-attachment-mutool-execution"
        or request["requested_scope"]
        != "two_pass_local_mupdf_text_derivation_for_exact_three_request_11872_attachments_only"
    ):
        raise ValueError("MuPDF request identity is invalid")
    if any(
        request[key] is not False
        for key in (
            "authorization_present",
            "pdf_processing_allowed",
            "derived_content_creation_allowed",
            "context_presentation_allowed",
            "analyst_execution_allowed",
            "reconciliation_allowed",
            "empirical_evidence",
            "human_reviewed",
            "gold_eligible",
        )
    ):
        raise ValueError("MuPDF request is not inert")
    if (
        request["method"] != auth["method"]
        or request["method_approval"] != auth["method_approval"]
        or request["wrapper"] != auth["wrapper"]
    ):
        raise ValueError("MuPDF authorization pins differ from request")

    method = _object(method_path)
    approval = _object(approval_path)
    approval_keys = {
        "schema_version",
        "approval_id",
        "status",
        "approved_by",
        "approved_on",
        "recorded_at",
        "recording_note",
        "approval_statement",
        "approval_statement_sha256",
        "approved_candidate",
        "approved_scope",
        "method_approved",
        "wrapper_creation_allowed",
        "authorization_request_creation_allowed",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "prohibited_actions",
    }
    if set(approval) != approval_keys:
        raise ValueError("MuPDF method approval structure is not exact")
    if (
        approval["schema_version"]
        != "foi-o.bounded-pilot-attachment-alternative-text-method-approval.v0.1.0"
        or approval["approval_id"]
        != "bounded-pilot-11872-attachment-alternative-text-method-approved"
        or approval["approved_by"] != "edithatogo"
        or approval["approved_on"] != "2026-07-19"
        or not isinstance(approval["recorded_at"], str)
        or approval["recording_note"]
        != "recorded_at is repository provenance and is not claimed as approval time"
        or approval["approved_scope"]
        != "alternative_method_design_and_local_mupdf_wrapper_and_execution_authorization_request_creation_only"
        or approval["prohibited_actions"] != METHOD_APPROVAL_PROHIBITED_ACTIONS
    ):
        raise ValueError("MuPDF method approval provenance or scope is not exact")
    approved_candidate = approval.get("approved_candidate")
    if not isinstance(approved_candidate, dict) or set(approved_candidate) != {
        "path",
        "sha256",
        "repository_commit",
    }:
        raise ValueError("MuPDF method approval candidate pin is malformed")
    if approved_candidate["path"] != METHOD_RELATIVE_PATH or approved_candidate[
        "sha256"
    ] != _digest(method_path):
        raise ValueError("MuPDF method approval candidate pin mismatch")
    statement = approval.get("approval_statement")
    if (
        not isinstance(statement, str)
        or not statement
        or sha256(statement.encode()).hexdigest() != approval.get("approval_statement_sha256")
    ):
        raise ValueError("MuPDF method approval statement is invalid")
    if (
        approval.get("status")
        != "approved_alternative_method_and_inert_wrapper_request_creation_only"
        or approval.get("method_approved") is not True
        or approval.get("wrapper_creation_allowed") is not True
        or approval.get("authorization_request_creation_allowed") is not True
    ):
        raise ValueError("MuPDF method approval scope is absent")
    if any(
        approval.get(key) is not False
        for key in (
            "pdf_processing_allowed",
            "derived_content_creation_allowed",
            "context_presentation_allowed",
            "analyst_execution_allowed",
            "reconciliation_allowed",
            "empirical_evidence",
            "human_reviewed",
            "gold_eligible",
        )
    ):
        raise ValueError("MuPDF method approval scope is excessive")
    candidate_commit = approved_candidate["repository_commit"]
    candidate_bytes = subprocess.run(
        ["git", "show", f"{candidate_commit}:{METHOD_RELATIVE_PATH}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    if sha256(candidate_bytes).hexdigest() != approved_candidate["sha256"]:
        raise ValueError("MuPDF approved candidate commit does not contain pinned bytes")

    semantic_fields = (
        "sources",
        "method_tool",
        "runtime_observation",
        "environment",
        "argv_template",
        "output_contract",
        "failure_contract",
    )
    if any(request[field] != method[field] for field in semantic_fields):
        raise ValueError("MuPDF request differs from approved method")
    wrapper_commit = request["wrapper_repository_commit"]
    if not isinstance(wrapper_commit, str) or len(wrapper_commit) != 40:
        raise ValueError("MuPDF wrapper commit is invalid")
    wrapper_bytes = subprocess.run(
        ["git", "show", f"{wrapper_commit}:{WRAPPER_RELATIVE_PATH}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    if (
        sha256(wrapper_bytes).hexdigest() != wrapper_pin["sha256"]
        or wrapper_bytes != wrapper_path.read_bytes()
    ):
        raise ValueError("MuPDF wrapper commit does not contain exact current bytes")

    human = _object(human_path)
    human_keys = {
        "schema_version",
        "approved_by",
        "approved_on",
        "approval_statement",
        "approval_statement_sha256",
        "approved_request",
        "source_root",
        "output_directory",
        "prohibited_actions",
    }
    human_statement = human.get("approval_statement")
    if (
        set(human) != human_keys
        or human.get("schema_version")
        != "foi-o.bounded-pilot-attachment-mutool-human-approval.v0.1.0"
        or human.get("approved_by") != "human:edithatogo"
    ):
        raise ValueError("MuPDF human approval structure is not exact")
    if (
        not isinstance(human_statement, str)
        or not human_statement
        or sha256(human_statement.encode()).hexdigest() != human.get("approval_statement_sha256")
        or not human.get("approved_on")
    ):
        raise ValueError("MuPDF human approval statement is invalid")
    if (
        human["approved_request"] != request_pin
        or human["prohibited_actions"] != PROHIBITED_ACTIONS
    ):
        raise ValueError("MuPDF human approval scope is not exact")

    source = source_root.resolve(strict=True)
    output_parent = output_directory.parent.resolve(strict=True)
    output = output_parent / output_directory.name
    if source_root.absolute() != source or output_directory.parent.absolute() != output_parent:
        raise ValueError("MuPDF bound paths contain symlink ancestors")
    if output.exists() or output.is_symlink() or output_directory.name in {"", ".", ".."}:
        raise ValueError("MuPDF output must not exist")
    if any(
        a == b or a.is_relative_to(b) or b.is_relative_to(a)
        for a, b in ((root, source), (root, output), (source, output))
    ):
        raise ValueError("MuPDF bound paths overlap")
    if (
        request["source_root"] != str(source)
        or request["output_directory"] != str(output)
        or human["source_root"] != str(source)
        or human["output_directory"] != str(output)
        or str(source) != auth["source_root"]
        or str(output) != auth["output_directory"]
    ):
        raise ValueError("MuPDF paths do not match authorization")
    runtime = request["runtime_observation"]
    discovered = Path(runtime["discovered_path"])
    executable = Path(runtime["resolved_path"])
    if (
        not discovered.exists()
        or discovered.resolve(strict=True) != executable.resolve(strict=True)
        or not executable.resolve(strict=True).is_file()
        or _digest(executable) != runtime["executable_sha256"]
    ):
        raise ValueError("MuPDF executable identity mismatch")
    return VerifiedMutoolPermission(
        _token=_TOKEN,
        authorization_sha256=expected_authorization_sha256,
        repository_commit=expected_repository_commit,
        request_sha256=request_pin["sha256"],
        source_root=source,
        output_directory=output,
        executable_path=executable,
        executable_sha256=runtime["executable_sha256"],
    )


def _safe_source(root: Path, relative: str) -> Path:
    if "\\" in relative or "\0" in relative:
        raise ValueError("unsafe source path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(p in {"", ".", ".."} for p in pure.parts):
        raise ValueError("unsafe source path")
    current = root
    for part in pure.parts:
        current /= part
        if stat.S_ISLNK(current.lstat().st_mode):
            raise ValueError("source path contains a symlink")
    path = current.resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("source is not an in-root file")
    return path


def _validate_sources(request: dict[str, Any]) -> None:
    """Reject ambiguous or path-bearing output names before any source read."""
    sources = request.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("MuPDF request sources are not exact")
    names: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError("MuPDF source entry is not an object")
        required = {"relative_path", "sha256", "size", "output_name"}
        if not required.issubset(source):
            raise ValueError("MuPDF source entry is incomplete")
        name = source["output_name"]
        if (
            not isinstance(name, str)
            or name != f"attachment-{index:03d}.txt"
            or PurePosixPath(name).name != name
            or name in names
        ):
            raise ValueError("MuPDF output name is unsafe")
        if not isinstance(source["size"], int) or source["size"] <= 0:
            raise ValueError("MuPDF source size is invalid")
        digest = source["sha256"]
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("MuPDF source digest is invalid")
        names.add(name)


def _freeze(request: dict[str, Any], root: Path, directory: Path) -> list[_Frozen]:
    frozen: list[_Frozen] = []
    try:
        for index, source in enumerate(request["sources"]):
            original = _safe_source(root, source["relative_path"])
            descriptor = os.open(original, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                info = os.fstat(descriptor)
                data = bytearray()
                while chunk := os.read(descriptor, 1024 * 1024):
                    data.extend(chunk)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_size != source["size"]
                    or sha256(data).hexdigest() != source["sha256"]
                ):
                    raise ValueError("source identity mismatch")
                copy = directory / f"source-{index:03d}.pdf"
                fd = os.open(copy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                frozen.append(_Frozen(source, original, descriptor, info.st_dev, info.st_ino, copy))
            except Exception:
                os.close(descriptor)
                raise
    except Exception:
        for item in frozen:
            os.close(item.descriptor)
        raise
    return frozen


def _recheck(item: _Frozen) -> None:
    path_info = item.original.lstat()
    if stat.S_ISLNK(path_info.st_mode) or (path_info.st_dev, path_info.st_ino) != (
        item.device,
        item.inode,
    ):
        raise ValueError("source identity changed")
    digest = sha256()
    offset = 0
    while chunk := os.pread(item.descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    if (
        os.fstat(item.descriptor).st_size != item.source["size"]
        or digest.hexdigest() != item.source["sha256"]
    ):
        raise ValueError("source content changed")


def _freeze_executable(permission: VerifiedMutoolPermission, directory: Path) -> _FrozenExecutable:
    original = permission.executable_path
    descriptor = os.open(original, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("MuPDF executable is not a regular file")
        data = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            data.extend(chunk)
        if sha256(data).hexdigest() != permission.executable_sha256:
            raise ValueError("MuPDF executable changed before freeze")
        copy = directory / "mutool"
        fd = os.open(copy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return _FrozenExecutable(
            original,
            descriptor,
            info.st_dev,
            info.st_ino,
            permission.executable_sha256,
            copy,
        )
    except Exception:
        os.close(descriptor)
        raise


def _recheck_executable(item: _FrozenExecutable) -> None:
    path_info = item.original.lstat()
    if stat.S_ISLNK(path_info.st_mode) or (path_info.st_dev, path_info.st_ino) != (
        item.device,
        item.inode,
    ):
        raise ValueError("MuPDF executable identity changed")
    digest = sha256()
    offset = 0
    while chunk := os.pread(item.descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    if digest.hexdigest() != item.digest:
        raise ValueError("MuPDF executable content changed")


def _rename_no_replace(source: Path, destination: Path) -> None:
    """Atomically install a directory without replacing any destination."""
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        result = libc.renamex_np(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        result = libc.renameat2(-100, source_bytes, -100, destination_bytes, 1)  # RENAME_NOREPLACE
    else:
        raise ValueError("atomic no-replace installation is unsupported")
    if result != 0:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise ValueError("MuPDF output appeared before atomic install")
        raise OSError(error, os.strerror(error), destination)


def _run(
    executable: Path,
    source: Path,
    target: Path,
    stderr: Path,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> int:
    fd = os.open(stderr, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as errors:
        process = subprocess.Popen(
            [str(executable), "draw", "-q", "-F", "txt", "-o", str(target), str(source)],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=errors,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise ValueError("MuPDF extraction timed out") from None
    return returncode


def _reverify(permission: VerifiedMutoolPermission, root: Path) -> dict[str, Any]:
    refreshed = verify_mutool_pre_execution(
        repository_root=root,
        authorization_path=root / AUTHORIZATION_RELATIVE_PATH,
        expected_authorization_sha256=permission.authorization_sha256,
        expected_repository_commit=permission.repository_commit,
        source_root=permission.source_root,
        output_directory=permission.output_directory,
    )
    if refreshed != permission:
        raise ValueError("MuPDF permission bindings changed")
    return _object(_repo_file(root, REQUEST_RELATIVE_PATH))


def derive_attachment_text_with_mutool(
    *,
    permission: VerifiedMutoolPermission,
    repository_root: Path,
    source_root: Path,
    output_directory: Path,
) -> MutoolDerivationResult:
    """Execute the exact two-pass MuPDF contract and atomically install it."""
    if not isinstance(permission, VerifiedMutoolPermission):
        raise ValueError("verified MuPDF permission is required")
    root = repository_root.resolve(strict=True)
    source = source_root.resolve(strict=True)
    output = output_directory.parent.resolve(strict=True) / output_directory.name
    if source != permission.source_root or output != permission.output_directory:
        raise ValueError("MuPDF paths differ from authorization")
    if output.exists() or output.is_symlink():
        raise ValueError("MuPDF output directory must not exist")
    request = _reverify(permission, root)
    _validate_sources(request)
    workspace = Path(tempfile.mkdtemp(prefix=".foio-mutool-work-", dir=output.parent))
    workspace.chmod(0o700)
    frozen: list[_Frozen] = []
    frozen_executable: _FrozenExecutable | None = None
    passes: list[list[bytes]] = []
    try:
        frozen_dir = workspace / "frozen"
        frozen_dir.mkdir(mode=0o700)
        frozen = _freeze(request, source, frozen_dir)
        frozen_executable = _freeze_executable(permission, frozen_dir)
        for pass_number in (1, 2):
            pass_dir = workspace / f"pass-{pass_number}"
            pass_dir.mkdir(mode=0o700)
            values: list[bytes] = []
            for index, item in enumerate(frozen):
                request = _reverify(permission, root)
                _recheck(item)
                _recheck_executable(frozen_executable)
                target = pass_dir / item.source["output_name"]
                stderr = pass_dir / f"stderr-{index:03d}.bin"
                returncode = _run(
                    frozen_executable.copy,
                    item.copy,
                    target,
                    stderr,
                    pass_dir,
                    dict(request["environment"]),
                    request["failure_contract"]["timeout_seconds"],
                )
                _recheck(item)
                error_bytes = stderr.read_bytes()
                stderr.unlink()
                stderr_digest = sha256(error_bytes).hexdigest()
                stderr_count = len(error_bytes)
                if returncode != 0:
                    raise ValueError(
                        "MuPDF extraction returned nonzero; "
                        f"stderr_sha256={stderr_digest}; stderr_byte_count={stderr_count}"
                    )
                if error_bytes:
                    raise ValueError(
                        "MuPDF extraction emitted stderr; "
                        f"stderr_sha256={stderr_digest}; stderr_byte_count={stderr_count}"
                    )
                info = target.lstat()
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("MuPDF output is not regular")
                target.chmod(0o600)
                data = target.read_bytes()
                if not data:
                    raise ValueError("MuPDF output is empty")
                data.decode("utf-8", errors="strict")
                values.append(data)
            passes.append(values)
        if passes[0] != passes[1]:
            raise ValueError("MuPDF repeat outputs do not match")
        manifest = {
            "schema_version": "foi-o.bounded-pilot-attachment-mutool-result.v0.1.0",
            "status": "local_derivation_complete_context_still_prohibited",
            "authorization_sha256": permission.authorization_sha256,
            "repository_commit": permission.repository_commit,
            "execution_request_sha256": permission.request_sha256,
            "outputs": [
                {
                    "output_name": s["output_name"],
                    "source_sha256": s["sha256"],
                    "output_sha256": sha256(data).hexdigest(),
                    "byte_count": len(data),
                    "repeat_outputs_match": True,
                }
                for s, data in zip(request["sources"], passes[1], strict=True)
            ],
            "local_only": True,
            "context_presentation_allowed": False,
            "analyst_execution_allowed": False,
            "reconciliation_allowed": False,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
        }
        manifest_path = workspace / "pass-2" / "derivation-manifest.json"
        fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(
                (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
            )
            stream.flush()
            os.fsync(stream.fileno())
        _reverify(permission, root)
        _recheck_executable(frozen_executable)
        for item in frozen:
            _recheck(item)
        _rename_no_replace(workspace / "pass-2", output)
        return MutoolDerivationResult(output, manifest)
    finally:
        for item in frozen:
            os.close(item.descriptor)
        if frozen_executable is not None:
            os.close(frozen_executable.descriptor)
        shutil.rmtree(workspace, ignore_errors=True)
