import json
import runpy
from pathlib import Path
from subprocess import run

import pytest

from foi_o_nz import bounded_pilot_execution as execution
from foi_o_nz import bounded_pilot_stage_runtime as runtime
from foi_o_nz.bounded_pilot_empirical_results import ANALYST_IDS, canonical_sha256

HELPERS = runpy.run_path(str(Path(__file__).with_name("test_bounded_pilot_empirical_results.py")))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    run(["git", "init", "-q"], cwd=repo, check=True)
    roles = {
        "analyst_a": {
            "actor_id": ANALYST_IDS[0],
            "canonical_locator": "/root/synthetic-a",
            "prompt": {"sha256": "a" * 64},
        },
        "analyst_b": {
            "actor_id": ANALYST_IDS[1],
            "canonical_locator": "/root/synthetic-b",
            "prompt": {"sha256": "b" * 64},
        },
        "reconciler": {
            "actor_id": runtime.RECONCILER_ID,
            "canonical_locator": "/root/synthetic-reconciler",
            "prompt": {"sha256": "9" * 64},
        },
    }
    _write(repo / "request.json", {"roles": roles})
    _write(
        repo / "plan.json",
        {
            "governed_inputs": {
                "analyst_request": {"path": "request.json", "sha256": "0" * 64},
                "codebook": {"path": "codebook.json", "sha256": "2" * 64},
            }
        },
    )
    _write(repo / "codebook.json", {})
    _write(repo / "auth.json", {"plan": {"path": "plan.json", "sha256": "0" * 64}})
    paths = {
        "analyst_a": "handshake-a.json",
        "analyst_b": "handshake-b.json",
        "reconciler": "handshake-r.json",
    }
    evidence_pins = []
    for key, relative in paths.items():
        role = roles[key]
        reply = {
            "actor_id": role["actor_id"],
            "actor_class": "automated_agent",
            "role": "reconciler" if key == "reconciler" else "analyst",
            "provider": "OpenAI",
            "model": "Codex synthetic test runtime",
            "session_id": role["canonical_locator"],
            "role_prompt_sha256": role["prompt"]["sha256"],
            "handshake_prompt_sha256": "f" * 64,
            "context_received": False,
            "candidate_labels_received": False,
            "peer_outputs_received": False,
            "ready_for_future_exact_authorization": True,
        }
        _write(
            repo / relative,
            {
                "schema_version": "foi-o.bounded-pilot-runtime-handshake-evidence.v0.2.0",
                "status": "locked_context_free_runtime_handshake",
                "actor_id": role["actor_id"],
                "actor_class": "automated_agent",
                "role": "reconciler" if key == "reconciler" else "analyst",
                "provider": "OpenAI",
                "model": "Codex synthetic test runtime",
                "session_id": role["canonical_locator"],
                "role_prompt_sha256": role["prompt"]["sha256"],
                "handshake_prompt": {
                    "path": "prompt",
                    "sha256": "f" * 64,
                    "repository_commit": "0" * 40,
                },
                "reply_sha256": runtime.sha256(
                    json.dumps(reply, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "context_received": False,
                "candidate_labels_received": False,
                "peer_outputs_received": False,
                "ready_for_future_exact_authorization": True,
                "local_only": True,
                "execution_authorized": False,
                "empirical_result_approved": False,
            },
        )
        evidence_pins.append(
            {
                "actor_id": role["actor_id"],
                "path": relative,
                "sha256": runtime.sha256((repo / relative).read_bytes()).hexdigest(),
            }
        )
    readiness_path = "readiness.json"
    _write(repo / readiness_path, {"evidence": evidence_pins})
    run(["git", "add", "."], cwd=repo, check=True)
    run(
        [
            "git",
            "-c",
            "user.name=X",
            "-c",
            "user.email=x@example.invalid",
            "commit",
            "-qm",
            "runtime",
        ],
        cwd=repo,
        check=True,
    )
    head = run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    monkeypatch.setattr(runtime, "HANDSHAKE_READINESS_PATH", readiness_path)
    monkeypatch.setattr(
        runtime,
        "HANDSHAKE_READINESS_SHA256",
        runtime.sha256((repo / readiness_path).read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(runtime, "HANDSHAKE_READINESS_COMMIT", head)
    workspace = tmp_path / "workspace"
    workspace.mkdir(mode=0o700)
    manifest = HELPERS["_manifest"]()
    manifest_path = workspace / "context-manifest.locked.json"
    manifest_path.write_bytes(runtime._strict_bytes(manifest))
    manifest_path.chmod(0o600)
    permission = execution.StagePermission(
        _token=execution._TOKEN,
        authorization_sha256="1" * 64,
        repository_commit=head,
        repository_root=repo,
        authorization_path=repo / "auth.json",
        workspace=workspace,
        source_roots={},
        evidence_manifest={},
        derivation_result={},
        unit_sha256_by_request={},
        stage="S2_CONTEXT_MATERIALIZATION",
        reconciliation_allowed=False,
    )
    monkeypatch.setattr(
        execution,
        "verify_materialized_contexts",
        lambda _, **kwargs: execution.ContextLock(
            workspace, "c" * 64, "d" * 64, "S3_ANALYST_EXECUTION"
        ),
    )
    a, b, _ = HELPERS["_sets"]()
    records_a = [entry["record"] for entry in a["entries"]]
    records_b = [entry["record"] for entry in b["entries"]]
    return permission, records_a, records_b, manifest


def test_atomic_dual_lock_then_disagreement_only_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    permission, records_a, records_b, manifest = _fixture(tmp_path, monkeypatch)
    locked = runtime.lock_dual_analysis(
        permission, analyst_a_records=records_a, analyst_b_records=records_b
    )
    assert locked.disagreement_request_ids == ("11872",)
    assert {path.name for path in locked.directory.iterdir()} == {
        *runtime.ANALYSIS_NAMES,
        runtime.LOCK_NAME,
    }
    a = json.loads((locked.directory / runtime.ANALYSIS_NAMES[0]).read_text())
    b = json.loads((locked.directory / runtime.ANALYSIS_NAMES[1]).read_text())
    lock = json.loads((locked.directory / runtime.LOCK_NAME).read_text())
    helper_globals = HELPERS["_reconciliation"].__globals__
    helper_globals["PATHS"] = tuple(f"analysis/{name}" for name in runtime.ANALYSIS_NAMES)
    helper_globals["LOCK_PATH"] = f"analysis/{runtime.LOCK_NAME}"
    reconciliation = HELPERS["_reconciliation"](a, b, lock, manifest)
    raw = [entry["record"] for entry in reconciliation["entries"]]
    result = runtime.reconcile_and_diagnose(permission, reconciler_records=raw)
    assert {path.name for path in result.directory.iterdir()} == {
        runtime.RECONCILIATION_NAME,
        runtime.DIAGNOSTICS_NAME,
    }
    assert result.empirical_result_approved is False
    assert result.publication_allowed is False


def test_invalid_second_set_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    permission, records_a, records_b, _ = _fixture(tmp_path, monkeypatch)
    records_b[1]["label"] = "not-approved"
    with pytest.raises(ValueError, match="vocabulary"):
        runtime.lock_dual_analysis(
            permission, analyst_a_records=records_a, analyst_b_records=records_b
        )
    assert not (permission.workspace / "analysis").exists()


def test_reconciler_cannot_skip_or_expand_disagreements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    permission, records_a, records_b, _ = _fixture(tmp_path, monkeypatch)
    runtime.lock_dual_analysis(permission, analyst_a_records=records_a, analyst_b_records=records_b)
    with pytest.raises(ValueError, match="disagreement-only"):
        runtime.reconcile_and_diagnose(permission, reconciler_records=[])
    assert not (permission.workspace / "reconciliation").exists()


def test_committed_handshake_and_locked_set_tampering_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    permission, records_a, records_b, _ = _fixture(tmp_path, monkeypatch)
    runtime.lock_dual_analysis(permission, analyst_a_records=records_a, analyst_b_records=records_b)
    path = permission.workspace / "analysis" / runtime.ANALYSIS_NAMES[0]
    value = json.loads(path.read_text())
    value["entries"][0]["record_sha256"] = "0" * 64
    path.write_bytes(runtime._strict_bytes(value))
    path.chmod(0o600)
    with pytest.raises(ValueError, match=r"hash|lock|mismatch"):
        runtime.reconcile_and_diagnose(permission, reconciler_records=[])
    assert canonical_sha256(value) != "0" * 64
