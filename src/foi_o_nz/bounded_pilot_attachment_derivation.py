"""Fail-closed bounded-pilot attachment derivation machinery.

The executor is unreachable without an exact, committed authorization verified
against a clean repository checkout. Merely importing this module never reads a
source attachment or invokes the extraction tool.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

AUTHORIZATION_RELATIVE_PATH = (
    "examples/v2/bounded-pilot-attachment-derivation-execution-authorization.approved.json"
)
REQUEST_RELATIVE_PATH = (
    "examples/v2/bounded-pilot-attachment-derivation-execution-request.pending.json"
)
WRAPPER_RELATIVE_PATH = "src/foi_o_nz/bounded_pilot_attachment_derivation.py"
_PERMISSION_TOKEN = object()
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


@dataclass(frozen=True, slots=True, init=False)
class VerifiedAttachmentDerivationPermission:
    """Permission minted only after successful clean-HEAD verification."""

    authorization_sha256: str
    repository_commit: str
    request_sha256: str
    source_root: Path
    output_directory: Path
    executable_path: Path
    executable_sha256: str

    def __init__(
        self,
        *,
        authorization_sha256: str,
        repository_commit: str,
        request_sha256: str,
        source_root: Path,
        output_directory: Path,
        executable_path: Path,
        executable_sha256: str,
        _token: object,
    ) -> None:
        """Reject construction unless called by the verifier in this module."""
        if _token is not _PERMISSION_TOKEN:
            raise ValueError("attachment derivation permission cannot be constructed directly")
        object.__setattr__(self, "authorization_sha256", authorization_sha256)
        object.__setattr__(self, "repository_commit", repository_commit)
        object.__setattr__(self, "request_sha256", request_sha256)
        object.__setattr__(self, "source_root", source_root)
        object.__setattr__(self, "output_directory", output_directory)
        object.__setattr__(self, "executable_path", executable_path)
        object.__setattr__(self, "executable_sha256", executable_sha256)


@dataclass(frozen=True, slots=True)
class AttachmentDerivationResult:
    """Metadata-only result for a completed local derivation."""

    output_directory: Path
    manifest: dict[str, Any]


@dataclass(slots=True)
class _FrozenSource:
    source: dict[str, Any]
    original_path: Path
    descriptor: int
    device: int
    inode: int
    frozen_path: Path


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of exact file bytes."""
    return sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    """Load a JSON object or fail closed."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _git(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return completed.stdout.strip()


def _canonical_file(repository_root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("artifact path is unsafe")
    path = repository_root.joinpath(*pure.parts)
    current = repository_root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("artifact path contains a symlink")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(repository_root.resolve(strict=True)) or not resolved.is_file():
        raise ValueError("artifact path is not a canonical repository file")
    return resolved


def verify_attachment_derivation_pre_execution(
    *,
    repository_root: Path,
    authorization_path: Path,
    expected_authorization_sha256: str,
    expected_repository_commit: str,
    source_root: Path,
    output_directory: Path,
) -> VerifiedAttachmentDerivationPermission:
    """Verify an exact committed authorization and mint bounded permission."""
    root = repository_root.resolve(strict=True)
    canonical = _canonical_file(root, AUTHORIZATION_RELATIVE_PATH)
    if authorization_path.resolve(strict=True) != canonical:
        raise ValueError("attachment derivation authorization path is not canonical")
    if file_sha256(canonical) != expected_authorization_sha256:
        raise ValueError("attachment derivation authorization SHA-256 mismatch")
    head = _git(root, "rev-parse", "HEAD")
    if head != expected_repository_commit:
        raise ValueError("attachment derivation authorization commit is not HEAD")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("attachment derivation repository is not clean")
    tracked = _git(root, "ls-files", "--error-unmatch", AUTHORIZATION_RELATIVE_PATH)
    if tracked != AUTHORIZATION_RELATIVE_PATH:
        raise ValueError("attachment derivation authorization is not committed")

    authorization = load_object(canonical)
    expected_keys = {
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
    if set(authorization) != expected_keys:
        raise ValueError("attachment derivation authorization structure is not exact")
    if (
        authorization["schema_version"]
        != "foi-o.bounded-pilot-attachment-derivation-execution-authorization.v0.1.0"
        or authorization["status"] != "approved_exact_local_derivation"
        or not isinstance(authorization["authorization_id"], str)
        or not authorization["authorization_id"]
    ):
        raise ValueError("attachment derivation authorization identity is not exact")
    required_true = {
        "authorization_effective",
        "pdf_processing_allowed",
        "derived_content_creation_allowed",
        "local_only",
    }
    required_false = {
        "context_presentation_allowed",
        "analyst_execution_allowed",
        "reconciliation_allowed",
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
    }
    if any(authorization.get(key) is not True for key in required_true) or any(
        authorization.get(key) is not False for key in required_false
    ):
        raise ValueError("attachment derivation authorization scope is not exact")

    request_path = _canonical_file(root, REQUEST_RELATIVE_PATH)
    wrapper_path = _canonical_file(root, WRAPPER_RELATIVE_PATH)
    request_pin = authorization.get("execution_request")
    wrapper_pin = authorization.get("wrapper")
    if request_pin != {"path": REQUEST_RELATIVE_PATH, "sha256": file_sha256(request_path)}:
        raise ValueError("attachment derivation execution-request pin mismatch")
    if wrapper_pin != {"path": WRAPPER_RELATIVE_PATH, "sha256": file_sha256(wrapper_path)}:
        raise ValueError("attachment derivation wrapper pin mismatch")
    request = load_object(request_path)
    if (
        request.get("authorization_present") is not False
        or request.get("pdf_processing_allowed") is not False
    ):
        raise ValueError("attachment derivation execution request is not inert")
    for key in ("method", "method_approval"):
        if authorization[key] != request[key]:
            raise ValueError(f"attachment derivation governed {key} pin mismatch")
        pinned = _canonical_file(root, authorization[key]["path"])
        if file_sha256(pinned) != authorization[key]["sha256"]:
            raise ValueError(f"attachment derivation governed {key} digest mismatch")
    human_pin = authorization["human_approval"]
    if not isinstance(human_pin, dict) or set(human_pin) != {"path", "sha256"}:
        raise ValueError("attachment derivation human approval pin is malformed")
    human_path = _canonical_file(root, human_pin["path"])
    if file_sha256(human_path) != human_pin["sha256"]:
        raise ValueError("attachment derivation human approval pin mismatch")
    human = load_object(human_path)
    if (
        set(human)
        != {
            "schema_version",
            "approved_by",
            "approved_on",
            "approval_statement",
            "approval_statement_sha256",
            "approved_request",
            "prohibited_actions",
        }
        or human.get("schema_version")
        != "foi-o.bounded-pilot-attachment-derivation-human-approval.v0.1.0"
        or human.get("approved_by") != "human:edithatogo"
    ):
        raise ValueError("attachment derivation human approval structure is not exact")
    statement = human.get("approval_statement")
    if (
        not isinstance(statement, str)
        or not statement
        or sha256(statement.encode()).hexdigest() != human.get("approval_statement_sha256")
        or not isinstance(human.get("approved_on"), str)
        or not human["approved_on"]
    ):
        raise ValueError("attachment derivation human approval statement is invalid")
    if (
        human["approved_request"] != request_pin
        or human["prohibited_actions"] != PROHIBITED_ACTIONS
    ):
        raise ValueError("attachment derivation human approval scope is not exact")
    source_base = source_root.resolve(strict=True)
    output_parent = output_directory.parent.resolve(strict=True)
    output = output_parent / output_directory.name
    if source_root.absolute() != source_base or output_directory.parent.absolute() != output_parent:
        raise ValueError("attachment derivation bound paths contain symlink ancestors")
    if output.exists() or output.is_symlink() or output_directory.name in {"", ".", ".."}:
        raise ValueError("attachment derivation bound output must not exist")
    if any(
        a == b or a.is_relative_to(b) or b.is_relative_to(a)
        for a, b in ((root, source_base), (root, output), (source_base, output))
    ):
        raise ValueError("attachment derivation bound paths overlap")
    if authorization["source_root"] != str(source_base) or authorization["output_directory"] != str(
        output
    ):
        raise ValueError("attachment derivation authorization path binding mismatch")
    executable = Path(request["runtime_observation"]["resolved_path"]).resolve(strict=True)
    executable_digest = request["runtime_observation"]["executable_sha256"]
    if not executable.is_file() or file_sha256(executable) != executable_digest:
        raise ValueError("attachment derivation executable identity mismatch")
    return VerifiedAttachmentDerivationPermission(
        authorization_sha256=expected_authorization_sha256,
        repository_commit=head,
        request_sha256=file_sha256(request_path),
        source_root=source_base,
        output_directory=output,
        executable_path=executable,
        executable_sha256=executable_digest,
        _token=_PERMISSION_TOKEN,
    )


def _safe_source(source_root: Path, relative_path: str) -> Path:
    if "\\" in relative_path or "\x00" in relative_path:
        raise ValueError("attachment source path is unsafe")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("attachment source path is unsafe")
    current = source_root
    for part in pure.parts:
        current /= part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("attachment source path contains a symlink")
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(source_root) or not resolved.is_file():
        raise ValueError("attachment source is not a regular in-root file")
    return resolved


def _check_source(path: Path, source: dict[str, Any]) -> None:
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size != source["size"]:
        raise ValueError("attachment source size or type mismatch")
    if file_sha256(path) != source["sha256"]:
        raise ValueError("attachment source SHA-256 mismatch")


def _reverify_permission(
    permission: VerifiedAttachmentDerivationPermission, root: Path
) -> dict[str, Any]:
    refreshed = verify_attachment_derivation_pre_execution(
        repository_root=root,
        authorization_path=root / AUTHORIZATION_RELATIVE_PATH,
        expected_authorization_sha256=permission.authorization_sha256,
        expected_repository_commit=permission.repository_commit,
        source_root=permission.source_root,
        output_directory=permission.output_directory,
    )
    fields = (
        "authorization_sha256",
        "repository_commit",
        "request_sha256",
        "source_root",
        "output_directory",
        "executable_path",
        "executable_sha256",
    )
    if any(getattr(refreshed, field) != getattr(permission, field) for field in fields):
        raise ValueError("attachment derivation permission bindings changed")
    return load_object(_canonical_file(root, REQUEST_RELATIVE_PATH))


def _freeze_sources(
    request: dict[str, Any], source_base: Path, directory: Path
) -> list[_FrozenSource]:
    frozen: list[_FrozenSource] = []
    try:
        for index, source in enumerate(request["sources"]):
            original = _safe_source(source_base, source["relative_path"])
            descriptor = os.open(original, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                info = os.fstat(descriptor)
                if not stat.S_ISREG(info.st_mode) or info.st_size != source["size"]:
                    raise ValueError("attachment source descriptor identity mismatch")
                data = b""
                while chunk := os.read(descriptor, 1024 * 1024):
                    data += chunk
                if sha256(data).hexdigest() != source["sha256"]:
                    raise ValueError("attachment frozen source SHA-256 mismatch")
                frozen_path = directory / f"source-{index:03d}.pdf"
                fd = os.open(frozen_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb", closefd=True) as frozen_file:
                    frozen_file.write(data)
                    frozen_file.flush()
                    os.fsync(frozen_file.fileno())
                frozen.append(
                    _FrozenSource(
                        source, original, descriptor, info.st_dev, info.st_ino, frozen_path
                    )
                )
            except Exception:
                os.close(descriptor)
                raise
    except Exception:
        for item in frozen:
            os.close(item.descriptor)
        raise
    else:
        return frozen


def _recheck_frozen_source(item: _FrozenSource) -> None:
    descriptor_info = os.fstat(item.descriptor)
    path_info = item.original_path.lstat()
    if stat.S_ISLNK(path_info.st_mode) or (path_info.st_dev, path_info.st_ino) != (
        item.device,
        item.inode,
    ):
        raise ValueError("attachment original source identity changed")
    if descriptor_info.st_size != item.source["size"]:
        raise ValueError("attachment original source size changed")
    digest = sha256()
    offset = 0
    while chunk := os.pread(item.descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    if digest.hexdigest() != item.source["sha256"]:
        raise ValueError("attachment original source content changed")


def _run_tool(
    *,
    executable: Path,
    source: Path,
    target: Path,
    stderr_path: Path,
    cwd: Path,
    environment: dict[str, str],
    timeout: int,
) -> int:
    stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(stderr_fd, "wb", closefd=True) as stderr_file:
            process = subprocess.Popen(
                [
                    str(executable),
                    "-layout",
                    "-enc",
                    "UTF-8",
                    "-eol",
                    "unix",
                    str(source),
                    str(target),
                ],
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file,
                start_new_session=True,
            )
            try:
                return process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise ValueError("attachment derivation tool timed out") from None
    except Exception:
        if not stderr_path.exists():
            os.close(stderr_fd)
        raise


def _quarantine_stderr(
    *,
    output_parent: Path,
    stderr_path: Path,
    derived_target: Path,
    source: dict[str, Any],
    pass_number: int,
    source_index: int,
) -> Path:
    """Preserve restricted stderr diagnostics while destroying derived text."""
    stderr_data = stderr_path.read_bytes()
    if derived_target.exists() or derived_target.is_symlink():
        derived_target.unlink()
    quarantine = Path(tempfile.mkdtemp(prefix=".foio-attachment-diagnostic-", dir=output_parent))
    try:
        quarantine.chmod(0o700)
        diagnostic_name = f"stderr-pass-{pass_number}-source-{source_index:03d}.bin"
        diagnostic = quarantine / diagnostic_name
        stderr_path.replace(diagnostic)
        diagnostic.chmod(0o600)
        metadata = {
            "schema_version": "foi-o.bounded-pilot-attachment-stderr-diagnostic.v0.1.0",
            "status": "quarantined_local_diagnostic_review_required",
            "pass_number": pass_number,
            "source_index": source_index,
            "source_inventory_pointer": source.get("inventory_pointer"),
            "source_relative_path": source["relative_path"],
            "source_sha256": source["sha256"],
            "stderr_file": diagnostic_name,
            "stderr_sha256": sha256(stderr_data).hexdigest(),
            "stderr_byte_count": len(stderr_data),
            "derived_text_retained": False,
            "local_only": True,
            "restricted_diagnostic_committed": False,
            "context_presentation_allowed": False,
            "analyst_execution_allowed": False,
            "empirical_evidence": False,
        }
        metadata_path = quarantine / "diagnostic-metadata.json"
        metadata_fd = os.open(metadata_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(metadata_fd, "wb", closefd=True) as metadata_file:
            metadata_file.write(
                (
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    + "\n"
                ).encode("utf-8")
            )
            metadata_file.flush()
            os.fsync(metadata_file.fileno())
    except Exception:
        shutil.rmtree(quarantine, ignore_errors=True)
        raise
    else:
        return quarantine


def derive_attachment_text(
    *,
    permission: VerifiedAttachmentDerivationPermission,
    repository_root: Path,
    source_root: Path,
    output_directory: Path,
) -> AttachmentDerivationResult:
    """Run the exact two-pass local derivation after verified authorization."""
    if not isinstance(permission, VerifiedAttachmentDerivationPermission):
        raise ValueError("verified attachment derivation permission is required")
    root = repository_root.resolve(strict=True)
    source_base = source_root.resolve(strict=True)
    output_parent = output_directory.parent.resolve(strict=True)
    output = output_parent / output_directory.name
    if source_base != permission.source_root or output != permission.output_directory:
        raise ValueError("attachment derivation paths differ from authorization")
    if output.exists() or output.is_symlink():
        raise ValueError("attachment output directory must not exist")
    request = _reverify_permission(permission, root)
    environment = dict(request["environment"])
    workspace = Path(tempfile.mkdtemp(prefix=".foio-attachment-work-", dir=output_parent))
    workspace.chmod(0o700)
    outputs_by_pass: list[list[bytes]] = []
    stderr_by_pass: list[list[bytes]] = []
    frozen: list[_FrozenSource] = []
    try:
        frozen_directory = workspace / "frozen"
        frozen_directory.mkdir(mode=0o700)
        frozen = _freeze_sources(request, source_base, frozen_directory)
        for pass_index in range(2):
            pass_dir = workspace / f"pass-{pass_index + 1}"
            pass_dir.mkdir(mode=0o700)
            pass_outputs: list[bytes] = []
            pass_stderr: list[bytes] = []
            for index, item in enumerate(frozen):
                request = _reverify_permission(permission, root)
                _recheck_frozen_source(item)
                source = item.source
                target = pass_dir / source["output_name"]
                target.touch(mode=0o600, exist_ok=False)
                stderr_path = pass_dir / f"stderr-{index:03d}.bin"
                returncode = _run_tool(
                    executable=permission.executable_path,
                    source=item.frozen_path,
                    target=target,
                    stderr_path=stderr_path,
                    cwd=pass_dir,
                    environment=environment,
                    timeout=request["failure_contract"]["timeout_seconds"],
                )
                target.chmod(0o600)
                _recheck_frozen_source(item)
                if returncode != 0:
                    raise ValueError("attachment derivation tool returned nonzero")
                stderr_data = stderr_path.read_bytes()
                if stderr_data:
                    quarantine = _quarantine_stderr(
                        output_parent=output_parent,
                        stderr_path=stderr_path,
                        derived_target=target,
                        source=source,
                        pass_number=pass_index + 1,
                        source_index=index,
                    )
                    raise ValueError(
                        f"attachment derivation tool emitted stderr; diagnostic quarantined at {quarantine}"
                    )
                stderr_path.unlink()
                target_info = target.lstat()
                if not stat.S_ISREG(target_info.st_mode):
                    raise ValueError("attachment derivation output is not a regular file")
                data = target.read_bytes()
                if not data:
                    raise ValueError("attachment derivation output is empty")
                data.decode("utf-8", errors="strict")
                pass_outputs.append(data)
                pass_stderr.append(stderr_data)
            outputs_by_pass.append(pass_outputs)
            stderr_by_pass.append(pass_stderr)
        if outputs_by_pass[0] != outputs_by_pass[1] or stderr_by_pass[0] != stderr_by_pass[1]:
            raise ValueError("attachment derivation repeat outputs do not match")
        manifest_outputs = [
            {
                "output_name": source["output_name"],
                "source_sha256": source["sha256"],
                "output_sha256": sha256(data).hexdigest(),
                "byte_count": len(data),
                "codepoint_count": len(data.decode("utf-8")),
                "stderr_sha256": sha256(b"").hexdigest(),
                "stderr_byte_count": 0,
                "repeat_outputs_match": True,
            }
            for source, data in zip(request["sources"], outputs_by_pass[1], strict=True)
        ]
        manifest = {
            "schema_version": "foi-o.bounded-pilot-attachment-derivation-result.v0.1.0",
            "status": "local_derivation_complete_context_still_prohibited",
            "authorization_sha256": permission.authorization_sha256,
            "repository_commit": permission.repository_commit,
            "execution_request_sha256": permission.request_sha256,
            "outputs": manifest_outputs,
            "local_only": True,
            "restricted_outputs_committed": False,
            "context_presentation_allowed": False,
            "analyst_execution_allowed": False,
            "reconciliation_allowed": False,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
        }
        manifest_path = workspace / "pass-2" / "derivation-manifest.json"
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        manifest_fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(manifest_fd, "wb", closefd=True) as manifest_file:
            manifest_file.write(manifest_bytes)
            manifest_file.flush()
            os.fsync(manifest_file.fileno())
        _reverify_permission(permission, root)
        for item in frozen:
            _recheck_frozen_source(item)
        (workspace / "pass-2").replace(output)
        return AttachmentDerivationResult(output_directory=output, manifest=manifest)
    finally:
        for item in frozen:
            os.close(item.descriptor)
        shutil.rmtree(workspace, ignore_errors=True)


def build_attachment_derivation_execution_request(
    *, repository_root: Path, wrapper_path: str, wrapper_sha256: str
) -> dict[str, Any]:
    """Build an inert request from the exact approved method chain."""
    method_path = repository_root / "examples/v2/bounded-pilot-attachment-text-method.pending.json"
    approval_path = (
        repository_root / "examples/v2/bounded-pilot-attachment-text-method-approval.approved.json"
    )
    method = load_object(method_path)
    approval = load_object(approval_path)
    if file_sha256(method_path) != approval["approved_candidate"]["sha256"]:
        raise ValueError("approved method candidate digest mismatch")
    if not approval["method_approved"] or approval["pdf_processing_allowed"]:
        raise ValueError("method approval scope is not fail-closed")
    if not wrapper_path.startswith("src/foi_o_nz/") or not wrapper_path.endswith(".py"):
        raise ValueError("wrapper path is outside the package")
    if len(wrapper_sha256) != 64:
        raise ValueError("wrapper digest is invalid")
    return {
        "schema_version": "foi-o.bounded-pilot-attachment-derivation-execution-request.v0.1.0",
        "request_id": "bounded-pilot-11872-attachment-derivation-execution",
        "status": "pending_exact_execution_authorization",
        "method": {
            "path": str(method_path.relative_to(repository_root)),
            "sha256": file_sha256(method_path),
        },
        "method_approval": {
            "path": str(approval_path.relative_to(repository_root)),
            "sha256": file_sha256(approval_path),
        },
        "wrapper": {"path": wrapper_path, "sha256": wrapper_sha256},
        "sources": method["sources"],
        "method_tool": method["method_tool"],
        "runtime_observation": method["runtime_observation"],
        "environment": method["environment"],
        "argv_template": method["argv_template"],
        "output_contract": method["output_contract"],
        "failure_contract": method["failure_contract"],
        "requested_scope": "two_pass_local_pdf_text_derivation_for_exact_three_request_11872_attachments_only",
        "authorization_present": False,
        "pdf_processing_allowed": False,
        "derived_content_creation_allowed": False,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
