import json
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.bounded_pilot_attachment_mutool_derivation import (
    AUTHORIZATION_RELATIVE_PATH,
    HUMAN_APPROVAL_RELATIVE_PATH,
    METHOD_APPROVAL_PROHIBITED_ACTIONS,
    METHOD_APPROVAL_RELATIVE_PATH,
    METHOD_RELATIVE_PATH,
    PROHIBITED_ACTIONS,
    REQUEST_RELATIVE_PATH,
    WRAPPER_RELATIVE_PATH,
    VerifiedMutoolPermission,
    derive_attachment_text_with_mutool,
    verify_mutool_pre_execution,
)

ROOT = Path(__file__).parents[1]


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _fixture(
    tmp_path: Path, tool_body: str = '/bin/cp "$7" "$6"'
) -> tuple[Path, Path, Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "x@example.invalid")
    _git(repo, "config", "user.name", "X")
    wrapper = repo / WRAPPER_RELATIVE_PATH
    wrapper.parent.mkdir(parents=True)
    wrapper.write_bytes((ROOT / WRAPPER_RELATIVE_PATH).read_bytes())
    source_root = tmp_path / "source"
    source = source_root / "attachments/synthetic.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic utf8\n")
    output = tmp_path / "derived" / "complete"
    output.parent.mkdir()
    tool = tmp_path / "mutool"
    tool_body = tool_body.replace("__TOOL__", str(tool)).replace("__OUTPUT__", str(output))
    tool.write_text(f"#!/bin/sh\n{tool_body}\n", encoding="utf-8")
    tool.chmod(0o700)
    sources = [
        {
            "relative_path": "attachments/synthetic.pdf",
            "sha256": _digest(source),
            "size": source.stat().st_size,
            "output_name": "attachment-000.txt",
        }
    ]
    runtime = {
        "discovered_path": str(tool),
        "resolved_path": str(tool),
        "executable_sha256": _digest(tool),
    }
    environment = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
    argv = ["mutool", "draw", "-q", "-F", "txt", "-o", "<output>", "<input>"]
    output_contract = {"repeat_runs_required": 2, "repeat_outputs_must_match": True}
    failure_contract = {"timeout_seconds": 2, "all_or_nothing": True}
    method = {
        "sources": sources,
        "method_tool": {"name": "mutool", "version": "synthetic"},
        "runtime_observation": runtime,
        "environment": environment,
        "argv_template": argv,
        "output_contract": output_contract,
        "failure_contract": failure_contract,
    }
    method_path = repo / METHOD_RELATIVE_PATH
    _write(method_path, method)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "synthetic method and wrapper")
    method_commit = _git(repo, "rev-parse", "HEAD")
    method_statement = "I approve synthetic method design only."
    method_approval = {
        "schema_version": "foi-o.bounded-pilot-attachment-alternative-text-method-approval.v0.1.0",
        "approval_id": "bounded-pilot-11872-attachment-alternative-text-method-approved",
        "status": "approved_alternative_method_and_inert_wrapper_request_creation_only",
        "approved_by": "edithatogo",
        "approved_on": "2026-07-19",
        "recorded_at": "2026-07-19T00:00:00Z",
        "recording_note": "recorded_at is repository provenance and is not claimed as approval time",
        "approval_statement": method_statement,
        "approval_statement_sha256": sha256(method_statement.encode()).hexdigest(),
        "approved_candidate": {
            "path": METHOD_RELATIVE_PATH,
            "sha256": _digest(method_path),
            "repository_commit": method_commit,
        },
        "approved_scope": "alternative_method_design_and_local_mupdf_wrapper_and_execution_authorization_request_creation_only",
        "method_approved": True,
        "wrapper_creation_allowed": True,
        "authorization_request_creation_allowed": True,
        "pdf_processing_allowed": False,
        "derived_content_creation_allowed": False,
        "context_presentation_allowed": False,
        "analyst_execution_allowed": False,
        "reconciliation_allowed": False,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "prohibited_actions": METHOD_APPROVAL_PROHIBITED_ACTIONS,
    }
    method_approval_path = repo / METHOD_APPROVAL_RELATIVE_PATH
    _write(method_approval_path, method_approval)
    method_pin = {"path": METHOD_RELATIVE_PATH, "sha256": _digest(method_path)}
    method_approval_pin = {
        "path": METHOD_APPROVAL_RELATIVE_PATH,
        "sha256": _digest(method_approval_path),
    }
    request = {
        "schema_version": "foi-o.bounded-pilot-attachment-mutool-execution-request.v0.1.0",
        "request_id": "bounded-pilot-11872-attachment-mutool-execution",
        "status": "pending_exact_execution_authorization",
        "method": method_pin,
        "method_approval": method_approval_pin,
        "wrapper": {"path": WRAPPER_RELATIVE_PATH, "sha256": _digest(wrapper)},
        "wrapper_repository_commit": method_commit,
        "source_root": str(source_root.resolve()),
        "output_directory": str(output.resolve()),
        "sources": sources,
        "method_tool": method["method_tool"],
        "runtime_observation": runtime,
        "environment": environment,
        "argv_template": argv,
        "output_contract": output_contract,
        "failure_contract": failure_contract,
        "requested_scope": "two_pass_local_mupdf_text_derivation_for_exact_three_request_11872_attachments_only",
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
    request_path = repo / REQUEST_RELATIVE_PATH
    _write(request_path, request)
    request_pin = {"path": REQUEST_RELATIVE_PATH, "sha256": _digest(request_path)}
    human_statement = "I approve exact synthetic execution for tests only."
    human = {
        "schema_version": "foi-o.bounded-pilot-attachment-mutool-human-approval.v0.1.0",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-19",
        "approval_statement": human_statement,
        "approval_statement_sha256": sha256(human_statement.encode()).hexdigest(),
        "approved_request": request_pin,
        "source_root": str(source_root.resolve()),
        "output_directory": str(output.resolve()),
        "prohibited_actions": PROHIBITED_ACTIONS,
    }
    human_path = repo / HUMAN_APPROVAL_RELATIVE_PATH
    _write(human_path, human)
    authorization = {
        "schema_version": "foi-o.bounded-pilot-attachment-mutool-execution-authorization.v0.1.0",
        "authorization_id": "synthetic",
        "status": "approved_exact_local_mutool_derivation",
        "execution_request": request_pin,
        "wrapper": {"path": WRAPPER_RELATIVE_PATH, "sha256": _digest(wrapper)},
        "method": method_pin,
        "method_approval": method_approval_pin,
        "human_approval": {"path": HUMAN_APPROVAL_RELATIVE_PATH, "sha256": _digest(human_path)},
        "source_root": str(source_root.resolve()),
        "output_directory": str(output.resolve()),
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
    auth = repo / AUTHORIZATION_RELATIVE_PATH
    _write(auth, authorization)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "synthetic")
    return repo, source_root, output, _digest(auth), _git(repo, "rev-parse", "HEAD")


def _permission(values: tuple[Path, Path, Path, str, str]):
    repo, source, output, digest, commit = values
    return verify_mutool_pre_execution(
        repository_root=repo,
        authorization_path=repo / AUTHORIZATION_RELATIVE_PATH,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        source_root=source,
        output_directory=output,
    )


def _commit_mutation(
    values: tuple[Path, Path, Path, str, str],
    *,
    request_change=None,
    human_change=None,
    method_approval_change=None,
) -> tuple[Path, Path, Path, str, str]:
    repo, source, output, _, _ = values
    request_path = repo / REQUEST_RELATIVE_PATH
    human_path = repo / HUMAN_APPROVAL_RELATIVE_PATH
    method_approval_path = repo / METHOD_APPROVAL_RELATIVE_PATH
    request = json.loads(request_path.read_text())
    human = json.loads(human_path.read_text())
    method_approval = json.loads(method_approval_path.read_text())
    if request_change:
        request_change(request)
    if method_approval_change:
        method_approval_change(method_approval)
        _write(method_approval_path, method_approval)
        request["method_approval"]["sha256"] = _digest(method_approval_path)
    _write(request_path, request)
    human["approved_request"]["sha256"] = _digest(request_path)
    if human_change:
        human_change(human)
    _write(human_path, human)
    auth_path = repo / AUTHORIZATION_RELATIVE_PATH
    auth = json.loads(auth_path.read_text())
    auth["execution_request"]["sha256"] = _digest(request_path)
    auth["method_approval"] = request["method_approval"]
    auth["human_approval"]["sha256"] = _digest(human_path)
    _write(auth_path, auth)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "synthetic mutation")
    return repo, source, output, _digest(auth_path), _git(repo, "rev-parse", "HEAD")


def test_permission_is_unforgeable() -> None:
    with pytest.raises(ValueError, match="cannot be constructed"):
        VerifiedMutoolPermission(_token=object())


def test_synthetic_two_pass_success_is_atomically_installed(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    permission = _permission(values)
    result = derive_attachment_text_with_mutool(
        permission=permission,
        repository_root=values[0],
        source_root=values[1],
        output_directory=values[2],
    )
    assert (result.output_directory / "attachment-000.txt").read_bytes() == b"synthetic utf8\n"
    assert result.manifest["context_presentation_allowed"] is False
    assert not list(values[2].parent.glob(".foio-mutool-work-*"))


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('echo warning >&2; /bin/cp "$7" "$6"', "emitted stderr"),
        ('printf "\\377" > "$6"', "codec"),
        (': > "$6"', "empty"),
        ("sleep 5", "timed out"),
        ("exit 4", "returned nonzero"),
    ],
)
def test_failures_leave_no_output_or_workspace(tmp_path: Path, body: str, message: str) -> None:
    values = _fixture(tmp_path, body)
    with pytest.raises((ValueError, UnicodeDecodeError), match=message):
        derive_attachment_text_with_mutool(
            permission=_permission(values),
            repository_root=values[0],
            source_root=values[1],
            output_directory=values[2],
        )
    assert not values[2].exists()
    assert not list(values[2].parent.glob(".foio-mutool-work-*"))


def test_dirty_repository_revokes_permission_before_execution(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    permission = _permission(values)
    (values[0] / "dirty").write_text("x")
    with pytest.raises(ValueError, match="not clean"):
        derive_attachment_text_with_mutool(
            permission=permission,
            repository_root=values[0],
            source_root=values[1],
            output_directory=values[2],
        )
    assert not values[2].exists()


def test_symlink_source_is_rejected(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    real = values[1] / "attachments/synthetic.pdf"
    moved = values[1] / "real.pdf"
    real.rename(moved)
    real.symlink_to(moved)
    with pytest.raises(ValueError, match="symlink"):
        derive_attachment_text_with_mutool(
            permission=_permission(values),
            repository_root=values[0],
            source_root=values[1],
            output_directory=values[2],
        )


def test_request_cannot_drift_from_approved_method(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    values = _commit_mutation(
        values,
        request_change=lambda request: request["environment"].update({"TZ": "Pacific/Auckland"}),
    )
    with pytest.raises(ValueError, match="differs from approved method"):
        _permission(values)


def test_human_approval_cannot_drop_a_prohibition(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    values = _commit_mutation(values, human_change=lambda human: human["prohibited_actions"].pop())
    with pytest.raises(ValueError, match="human approval scope"):
        _permission(values)


def test_method_approval_cannot_authorize_processing(tmp_path: Path) -> None:
    values = _fixture(tmp_path)
    values = _commit_mutation(
        values,
        method_approval_change=lambda approval: approval.update({"pdf_processing_allowed": True}),
    )
    with pytest.raises(ValueError, match="scope is excessive"):
        _permission(values)


def test_executable_mutation_during_run_is_detected_and_not_installed(tmp_path: Path) -> None:
    values = _fixture(
        tmp_path,
        "printf '#!/bin/sh\\nexit 9\\n' > '__TOOL__'; chmod 700 '__TOOL__'; /bin/cp \"$7\" \"$6\"",
    )
    with pytest.raises(
        ValueError, match=r"executable identity mismatch|executable content changed"
    ):
        derive_attachment_text_with_mutool(
            permission=_permission(values),
            repository_root=values[0],
            source_root=values[1],
            output_directory=values[2],
        )
    assert not values[2].exists()


def test_atomic_install_never_replaces_racing_destination(tmp_path: Path) -> None:
    from foi_o_nz.bounded_pilot_attachment_mutool_derivation import _rename_no_replace

    source = tmp_path / "ready"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "new").write_text("new")
    (destination / "owner").write_text("preserve")
    with pytest.raises(ValueError, match="appeared before atomic install"):
        _rename_no_replace(source, destination)
    assert (destination / "owner").read_text() == "preserve"
    assert (source / "new").read_text() == "new"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("approval_id", "drifted"),
        ("approved_by", "someone-else"),
        ("approved_scope", "broader"),
        ("prohibited_actions", []),
    ],
)
def test_method_approval_provenance_drift_is_rejected(
    tmp_path: Path, field: str, value: object
) -> None:
    values = _fixture(tmp_path)
    values = _commit_mutation(
        values,
        method_approval_change=lambda approval: approval.update({field: value}),
    )
    with pytest.raises(ValueError, match="approval provenance or scope"):
        _permission(values)


def test_stderr_failure_reports_only_hash_and_count_metadata(tmp_path: Path) -> None:
    values = _fixture(tmp_path, 'printf "secret warning" >&2; /bin/cp "$7" "$6"')
    with pytest.raises(ValueError, match="emitted stderr") as captured:
        derive_attachment_text_with_mutool(
            permission=_permission(values),
            repository_root=values[0],
            source_root=values[1],
            output_directory=values[2],
        )
    message = str(captured.value)
    assert "stderr_sha256=" in message
    assert "stderr_byte_count=14" in message
    assert "secret warning" not in message
    assert not values[2].exists()
