import json
import stat
import subprocess
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import foi_o_nz.bounded_pilot_attachment_derivation as derivation_module
from foi_o_nz.bounded_pilot_attachment_derivation import (
    AUTHORIZATION_RELATIVE_PATH,
    DIAGNOSTIC_AUTHORIZATION_RELATIVE_PATH,
    DIAGNOSTIC_HUMAN_APPROVAL_RELATIVE_PATH,
    DIAGNOSTIC_REQUEST_RELATIVE_PATH,
    REQUEST_RELATIVE_PATH,
    WRAPPER_RELATIVE_PATH,
    VerifiedAttachmentDerivationPermission,
    derive_attachment_text,
    verify_attachment_derivation_pre_execution,
    verify_attachment_diagnostic_pre_execution,
)

ROOT = Path(__file__).parents[1]


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _synthetic_repository(
    tmp_path: Path,
    *,
    tool_body: str = 'case "$6" in *"/sources/"*) exit 9;; esac\n/bin/cp "$6" "$7"',
    timeout: int = 10,
) -> tuple[Path, Path, Path, str, str]:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Test")
    wrapper = repository / WRAPPER_RELATIVE_PATH
    wrapper.parent.mkdir(parents=True)
    wrapper.write_bytes((ROOT / WRAPPER_RELATIVE_PATH).read_bytes())

    method_path = repository / "examples/v2/method.json"
    approval_path = repository / "examples/v2/method-approval.json"
    _write_json(method_path, {"method": "synthetic"})
    _write_json(approval_path, {"approval": "synthetic"})
    method_pin = {"path": "examples/v2/method.json", "sha256": _digest(method_path)}
    approval_pin = {
        "path": "examples/v2/method-approval.json",
        "sha256": _digest(approval_path),
    }

    source_root = tmp_path / "sources"
    relative_source = "content/attachments/synthetic.pdf"
    source = source_root / relative_source
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic PDF bytes only\n")

    tool = tmp_path / "fake-pdftotext"
    tool.write_text(f"#!/bin/sh\n{tool_body}\n", encoding="utf-8")
    tool.chmod(0o700)
    (tmp_path / "derived").mkdir()
    request = {
        "authorization_present": False,
        "pdf_processing_allowed": False,
        "method": method_pin,
        "method_approval": approval_pin,
        "wrapper": {"path": WRAPPER_RELATIVE_PATH, "sha256": _digest(wrapper)},
        "sources": [
            {
                "relative_path": relative_source,
                "sha256": _digest(source),
                "size": source.stat().st_size,
                "output_name": "attachment-000.txt",
            }
        ],
        "runtime_observation": {
            "resolved_path": str(tool),
            "executable_sha256": _digest(tool),
        },
        "environment": {"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "TZ": "UTC"},
        "failure_contract": {"timeout_seconds": timeout},
    }
    request_path = repository / REQUEST_RELATIVE_PATH
    _write_json(request_path, request)
    statement = "I approve the exact synthetic local derivation request for tests only."
    human_approval_path = repository / "examples/v2/human-approval.json"
    _write_json(
        human_approval_path,
        {
            "schema_version": "foi-o.bounded-pilot-attachment-derivation-human-approval.v0.1.0",
            "approved_by": "human:edithatogo",
            "approved_on": "2026-07-19",
            "approval_statement": statement,
            "approval_statement_sha256": sha256(statement.encode()).hexdigest(),
            "approved_request": {"path": REQUEST_RELATIVE_PATH, "sha256": _digest(request_path)},
            "prohibited_actions": derivation_module.PROHIBITED_ACTIONS,
        },
    )
    authorization = {
        "schema_version": "foi-o.bounded-pilot-attachment-derivation-execution-authorization.v0.1.0",
        "authorization_id": "synthetic-local-test",
        "status": "approved_exact_local_derivation",
        "execution_request": {"path": REQUEST_RELATIVE_PATH, "sha256": _digest(request_path)},
        "wrapper": {"path": WRAPPER_RELATIVE_PATH, "sha256": _digest(wrapper)},
        "method": method_pin,
        "method_approval": approval_pin,
        "human_approval": {
            "path": "examples/v2/human-approval.json",
            "sha256": _digest(human_approval_path),
        },
        "source_root": str(source_root.resolve()),
        "output_directory": str((tmp_path / "derived" / "complete").resolve()),
        "authorization_effective": True,
        "pdf_processing_allowed": True,
        "derived_content_creation_allowed": True,
        "local_only": True,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
    authorization_path = repository / AUTHORIZATION_RELATIVE_PATH
    _write_json(authorization_path, authorization)
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "synthetic authorization")
    commit = _git(repository, "rev-parse", "HEAD")
    return repository, source_root, authorization_path, _digest(authorization_path), commit


def _add_diagnostic_route(
    repository: Path, source_root: Path, output: Path
) -> tuple[Path, str, str]:
    base_request = json.loads((repository / REQUEST_RELATIVE_PATH).read_text(encoding="utf-8"))
    wrapper_commit = _git(repository, "log", "-1", "--format=%H", "--", WRAPPER_RELATIVE_PATH)
    wrapper_pin = {
        "path": WRAPPER_RELATIVE_PATH,
        "sha256": _digest(repository / WRAPPER_RELATIVE_PATH),
        "repository_commit": wrapper_commit,
    }
    request = {
        "schema_version": "foi-o.bounded-pilot-attachment-diagnostic-execution-request.v0.1.0",
        "request_id": "synthetic-diagnostic",
        "status": "pending_exact_diagnostic_authorization",
        "wrapper": wrapper_pin,
        "method": base_request["method"],
        "method_approval": base_request["method_approval"],
        "sources": base_request["sources"],
        "runtime_observation": base_request["runtime_observation"],
        "environment": base_request["environment"],
        "failure_contract": base_request["failure_contract"],
        "diagnostic_execution_allowed": False,
        "derived_content_retention_allowed": False,
    }
    request_path = repository / DIAGNOSTIC_REQUEST_RELATIVE_PATH
    _write_json(request_path, request)
    request_pin = {"path": DIAGNOSTIC_REQUEST_RELATIVE_PATH, "sha256": _digest(request_path)}
    statement = "I approve the exact synthetic diagnostic request for tests only."
    human_path = repository / DIAGNOSTIC_HUMAN_APPROVAL_RELATIVE_PATH
    _write_json(
        human_path,
        {
            "schema_version": "foi-o.bounded-pilot-attachment-diagnostic-human-approval.v0.1.0",
            "approved_by": "human:edithatogo",
            "approved_on": "2026-07-19",
            "approval_statement": statement,
            "approval_statement_sha256": sha256(statement.encode()).hexdigest(),
            "approved_request": request_pin,
            "bound_scope": {
                "source_root": str(source_root.resolve()),
                "output_directory": str(output.resolve()),
                "quarantine_parent": str(output.parent.resolve()),
                "diagnostic_only": True,
                "derived_content_retention_allowed": False,
            },
            "prohibited_actions": derivation_module.PROHIBITED_ACTIONS,
        },
    )
    authorization = {
        "schema_version": "foi-o.bounded-pilot-attachment-diagnostic-execution-authorization.v0.1.0",
        "authorization_id": "synthetic-diagnostic",
        "status": "approved_exact_local_diagnostic",
        "diagnostic_request": request_pin,
        "human_approval": {
            "path": DIAGNOSTIC_HUMAN_APPROVAL_RELATIVE_PATH,
            "sha256": _digest(human_path),
        },
        "wrapper": wrapper_pin,
        "method": request["method"],
        "method_approval": request["method_approval"],
        "source_root": str(source_root.resolve()),
        "output_directory": str(output.resolve()),
        "quarantine_parent": str(output.parent.resolve()),
        "diagnostic_execution_allowed": True,
        "pdf_processing_allowed": True,
        "transient_derived_content_allowed": True,
        "derived_content_retention_allowed": False,
        "local_only": True,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
    }
    authorization_path = repository / DIAGNOSTIC_AUTHORIZATION_RELATIVE_PATH
    _write_json(authorization_path, authorization)
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "synthetic diagnostic authorization")
    return authorization_path, _digest(authorization_path), _git(repository, "rev-parse", "HEAD")


def test_permission_cannot_be_constructed_directly() -> None:
    with pytest.raises(ValueError, match="cannot be constructed directly"):
        VerifiedAttachmentDerivationPermission(
            authorization_sha256="0" * 64,
            repository_commit="0" * 40,
            request_sha256="0" * 64,
            source_root=Path("/source"),
            output_directory=Path("/output"),
            executable_path=Path("/tool"),
            executable_sha256="0" * 64,
            authorization_relative_path=AUTHORIZATION_RELATIVE_PATH,
            request_relative_path=REQUEST_RELATIVE_PATH,
            quarantine_parent=Path("/quarantine"),
            diagnostic_only=False,
            _token=object(),
        )


def test_verifier_and_executor_complete_two_synthetic_passes(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(tmp_path)
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=tmp_path / "derived" / "complete",
    )
    output = tmp_path / "derived" / "complete"
    result = derive_attachment_text(
        permission=permission,
        repository_root=repository,
        source_root=source_root,
        output_directory=output,
    )
    expected = b"synthetic PDF bytes only\n"
    assert (output / "attachment-000.txt").read_bytes() == expected
    assert stat.S_IMODE((output / "attachment-000.txt").stat().st_mode) == 0o600
    assert stat.S_IMODE((output / "derivation-manifest.json").stat().st_mode) == 0o600
    assert not list(output.glob("stderr-*.bin"))
    assert result.manifest["outputs"][0]["output_sha256"] == sha256(expected).hexdigest()
    assert result.manifest["context_presentation_allowed"] is False
    assert not list(output.parent.glob(".foio-attachment-pass-*"))
    assert not list(output.parent.glob(".foio-attachment-work-*"))


@pytest.mark.parametrize("mutation", ["digest", "commit", "dirty", "scope"])
def test_verifier_rejects_authorization_or_checkout_drift(tmp_path: Path, mutation: str) -> None:
    repository, _, authorization, digest, commit = _synthetic_repository(tmp_path)
    if mutation == "digest":
        digest = "0" * 64
    elif mutation == "commit":
        commit = "0" * 40
    elif mutation == "dirty":
        (repository / WRAPPER_RELATIVE_PATH).write_text("dirty", encoding="utf-8")
    else:
        value = json.loads(authorization.read_text(encoding="utf-8"))
        value["context_presentation_allowed"] = True
        _write_json(authorization, value)
        _git(repository, "add", AUTHORIZATION_RELATIVE_PATH)
        _git(repository, "commit", "-m", "unsafe scope")
        commit = _git(repository, "rev-parse", "HEAD")
        digest = _digest(authorization)
    with pytest.raises(ValueError, match="attachment"):
        verify_attachment_derivation_pre_execution(
            repository_root=repository,
            authorization_path=authorization,
            expected_authorization_sha256=digest,
            expected_repository_commit=commit,
            source_root=repository.parent / "sources",
            output_directory=tmp_path / "derived" / "complete",
        )


def test_executor_rejects_symlinked_source_and_leaves_no_partial_output(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(tmp_path)
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=tmp_path / "derived" / "complete",
    )
    source = source_root / "content/attachments/synthetic.pdf"
    target = source_root / "real.pdf"
    source.replace(target)
    source.symlink_to(target)
    output = tmp_path / "derived" / "complete"
    with pytest.raises(ValueError, match="symlink"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".foio-attachment-pass-*"))


def test_executor_rejects_existing_output_without_touching_it(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(tmp_path)
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=tmp_path / "derived" / "complete",
    )
    output = tmp_path / "derived" / "complete"
    output.mkdir()
    marker = output / "keep"
    marker.write_text("untouched", encoding="utf-8")
    with pytest.raises(ValueError, match="must not exist"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert marker.read_text(encoding="utf-8") == "untouched"


def test_executor_rejects_executable_drift_after_verification(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(tmp_path)
    output = tmp_path / "derived" / "complete"
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    permission.executable_path.write_bytes(permission.executable_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="executable"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()


def test_executor_detects_original_replacement_during_tool_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(tmp_path)
    output = tmp_path / "derived" / "complete"
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    original_runner = derivation_module._run_tool

    def replacing_runner(**kwargs: Any) -> int:
        result = original_runner(**kwargs)
        source = source_root / "content/attachments/synthetic.pdf"
        replacement = source.with_suffix(".replacement")
        replacement.write_bytes(source.read_bytes())
        replacement.replace(source)
        return result

    monkeypatch.setattr(derivation_module, "_run_tool", replacing_runner)
    with pytest.raises(ValueError, match="identity changed"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".foio-attachment-work-*"))


def test_executor_kills_timed_out_process_group_and_cleans_up(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(
        tmp_path, tool_body="/bin/sleep 10", timeout=1
    )
    output = tmp_path / "derived" / "complete"
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    with pytest.raises(ValueError, match="timed out"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".foio-attachment-work-*"))


def test_nonempty_stderr_is_quarantined_without_derived_text(tmp_path: Path) -> None:
    repository, source_root, authorization, digest, commit = _synthetic_repository(
        tmp_path,
        tool_body='/bin/cp "$6" "$7"\n/bin/echo "synthetic warning" >&2',
    )
    output = tmp_path / "derived" / "complete"
    permission = verify_attachment_derivation_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    with pytest.raises(ValueError, match="diagnostic quarantined"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".foio-attachment-work-*"))
    quarantines = list(output.parent.glob(".foio-attachment-diagnostic-*"))
    assert len(quarantines) == 1
    quarantine = quarantines[0]
    assert stat.S_IMODE(quarantine.stat().st_mode) == 0o700
    stderr_files = list(quarantine.glob("stderr-*.bin"))
    assert len(stderr_files) == 1
    assert stat.S_IMODE(stderr_files[0].stat().st_mode) == 0o600
    assert stderr_files[0].read_bytes() == b"synthetic warning\n"
    assert not list(quarantine.glob("attachment-*.txt"))
    metadata_path = quarantine / "diagnostic-metadata.json"
    assert stat.S_IMODE(metadata_path.stat().st_mode) == 0o600
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["stderr_sha256"] == sha256(b"synthetic warning\n").hexdigest()
    assert metadata["stderr_byte_count"] == len(b"synthetic warning\n")
    assert metadata["source_sha256"] == _digest(source_root / "content/attachments/synthetic.pdf")
    assert metadata["source_relative_path"] == "content/attachments/synthetic.pdf"
    assert metadata["pass_number"] == 1
    assert metadata["derived_text_retained"] is False


def test_separate_diagnostic_route_mints_nonretaining_permission(tmp_path: Path) -> None:
    repository, source_root, _, _, _ = _synthetic_repository(
        tmp_path, tool_body='/bin/cp "$6" "$7"\n/bin/echo "diagnostic only" >&2'
    )
    output = tmp_path / "derived" / "complete"
    authorization, digest, commit = _add_diagnostic_route(repository, source_root, output)
    permission = verify_attachment_diagnostic_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    assert permission.diagnostic_only is True
    assert permission.request_relative_path == DIAGNOSTIC_REQUEST_RELATIVE_PATH
    with pytest.raises(ValueError, match="diagnostic quarantined"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert len(list(output.parent.glob(".foio-attachment-diagnostic-*"))) == 1


def test_diagnostic_route_destroys_text_when_stderr_is_empty(tmp_path: Path) -> None:
    repository, source_root, _, _, _ = _synthetic_repository(tmp_path)
    output = tmp_path / "derived" / "complete"
    authorization, digest, commit = _add_diagnostic_route(repository, source_root, output)
    permission = verify_attachment_diagnostic_pre_execution(
        repository_root=repository,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source_root,
        output_directory=output,
    )
    with pytest.raises(ValueError, match="no stderr; derived text destroyed"):
        derive_attachment_text(
            permission=permission,
            repository_root=repository,
            source_root=source_root,
            output_directory=output,
        )
    assert not output.exists()
    assert not list(output.parent.glob(".foio-attachment-diagnostic-*"))
