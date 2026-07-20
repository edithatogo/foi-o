import json
from hashlib import sha256
from pathlib import Path
from subprocess import run

import pytest

import foi_o_nz.bounded_pilot_execution as execution
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _commit(root: Path, message: str) -> str:
    run(["git", "add", "."], cwd=root, check=True)
    run(
        [
            "git",
            "-c",
            "user.name=Pilot",
            "-c",
            "user.email=x@example.invalid",
            "commit",
            "-qm",
            message,
        ],
        cwd=root,
        check=True,
    )
    return run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _pin(root: Path, path: str, commit: str | None = None) -> dict[str, str]:
    value = {"path": path, "sha256": _sha(root / path)}
    if commit:
        value["repository_commit"] = commit
    return value


def _blocks(text: str, values: list[str]) -> list[dict[str, object]]:
    result = []
    cursor = 0
    for index, value in enumerate(values):
        start = text.index(value, cursor)
        end = start + len(value)
        cursor = end
        result.append(
            {
                "element_id": f"block-{index}",
                "text_span": {"start": start, "end": end},
                "text_sha256": sha256(value.encode()).hexdigest(),
            }
        )
    return result


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, provenance_bridge: bool = False):
    root = tmp_path / "repo"
    root.mkdir()
    run(["git", "init", "-q"], cwd=root, check=True)
    local = tmp_path / "local"
    local.mkdir(mode=0o700)
    r1, r2, derived = local / "r1", local / "r2", local / "derived"
    context2 = local / "r2-context" if provenance_bridge else r2
    for directory in (r1 / "content", r2, context2 / "content", derived):
        directory.mkdir(parents=True, mode=0o700)
    page1 = "HEAD first MID second MID third MID fourth TAIL"
    page2 = "HEAD fifth TAIL"
    (r1 / "content/page.html").write_text(page1)
    (context2 / "content/page.html").write_text(page2)
    attachment_texts = ["attachment one", "attachment two", "attachment three"]
    outputs = []
    files = []
    for index, text in enumerate(attachment_texts):
        path = derived / f"attachment-{index:03d}.txt"
        path.write_text(text)
        path.chmod(0o600)
        source_sha = sha256(f"pdf-{index}".encode()).hexdigest()
        outputs.append(
            {
                "output_name": path.name,
                "source_sha256": source_sha,
                "output_sha256": _sha(path),
                "byte_count": path.stat().st_size,
            }
        )
        files.append({"sha256": source_sha})
    records = [
        {
            "request_id": "11872",
            "page_html_sha256": _sha(r1 / "content/page.html"),
            "correspondence": {
                "block_count": 4,
                "blocks": _blocks(page1, ["first", "second", "third", "fourth"]),
            },
            "attachments": {"verified_empty": False, "files": files},
        },
        {
            "request_id": "35076",
            "page_html_sha256": _sha(context2 / "content/page.html"),
            "correspondence": {"block_count": 1, "blocks": _blocks(page2, ["fifth"])},
            "attachments": {"verified_empty": True, "files": []},
        },
    ]
    if provenance_bridge:
        records[1]["snapshot_manifest_sha256"] = "9" * 64
        _json(
            r2 / "verification.json",
            {
                "source_manifest_sha256": "9" * 64,
                "source_content_sha256": records[1]["page_html_sha256"],
                "source_records_modified": False,
                "storage": "local_only",
            },
        )
    evidence_path = "meta/evidence.json"
    derivation_path = "meta/derivation.json"
    _json(root / evidence_path, {"request_ids": ["11872", "35076"], "records": records})
    _json(root / derivation_path, {"outputs": outputs})
    base_path = "meta/base.json"
    _json(
        root / base_path,
        {
            "artifacts": {"evidence_manifest": _pin(root, evidence_path)},
            "units": [
                {"request_id": "11872", "unit_sha256": "1" * 64},
                {"request_id": "35076", "unit_sha256": "2" * 64},
            ],
        },
    )
    base_commit = _commit(root, "base")
    candidate_path = "meta/candidate.json"
    _json(
        root / candidate_path,
        {
            "derived_from_readiness": _pin(root, base_path, base_commit),
            "attachment_derivation_result": _pin(root, derivation_path, base_commit),
        },
    )
    candidate_commit = _commit(root, "candidate")
    ready_path = "meta/ready.json"
    _json(root / ready_path, {"candidate": _pin(root, candidate_path, candidate_commit)})
    request_path = "meta/request.json"
    roles = {
        "analyst_a": {"actor_id": "agent:a"},
        "analyst_b": {"actor_id": "agent:b"},
        "reconciler": {"actor_id": "agent:r"},
    }
    _json(root / request_path, {"roles": roles})
    input_commit = _commit(root, "inputs")
    roots = {
        "request_11872_source": str(r1),
        "request_35076_source": str(r2),
        "derived_attachments": str(derived),
        "execution_workspace": str(local / "workspace"),
    }
    plan_path = "meta/plan.json"
    plan = {
        "status": "pending_single_exact_batched_execution_approval",
        "local_roots": roots,
        "context_contract": {"unit_order": ["11872", "35076"]},
        "governed_inputs": {
            "approved_readiness": _pin(root, ready_path, input_commit),
            "analyst_request": _pin(root, request_path, input_commit),
        },
    }
    _json(root / plan_path, plan)
    plan_commit = _commit(root, "plan")
    plan_pin = _pin(root, plan_path, plan_commit)
    approval_path = "meta/approval.json"
    statement = "exact omnibus approval"
    approval = {
        "schema_version": "foi-o.bounded-pilot-batched-execution-approval.v0.1.0",
        "approved_by": "human:edithatogo",
        "approved_on": "2026-07-20",
        "approval_statement": statement,
        "approval_statement_sha256": sha256(statement.encode()).hexdigest(),
        "approved_plan": plan_pin,
        "local_stage_contract_creation_authorized": True,
        "conditional_local_execution_authorized_after_exact_verification": True,
        "final_exact_results_and_package_approval_required": True,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "publication_allowed": False,
        "external_action_allowed": False,
    }
    _json(root / approval_path, approval)
    approval_commit = _commit(root, "approval")
    approval_pin = _pin(root, approval_path, approval_commit)
    auth = {
        "schema_version": "foi-o.bounded-pilot-batched-execution-authorization.v0.1.0",
        "authorization_id": "synthetic",
        "status": "approved_pending_exact_pre_execution_verification",
        "plan": plan_pin,
        "approval": approval_pin,
        "local_roots": roots,
        "context_contract": plan["context_contract"],
        "analyst_roles": {key: roles[key] for key in ("analyst_a", "analyst_b")},
        "reconciler_role": roles["reconciler"],
        "implementation_contracts": {"synthetic": _pin(root, request_path, input_commit)},
        "runtime_handshake_readiness": _pin(root, request_path, input_commit),
        "ordered_stages": [
            {"id": f"S{index}", "authorized": True, "failure_action": "stop_fail_closed"}
            for index in range(2, 9)
        ],
        "authorization_effective_after_verification": True,
        "context_materialization_authorized": True,
        "context_presentation_authorized": True,
        "analyst_execution_authorized": True,
        "reconciliation_authorized_conditionally": True,
        "candidate_manuscript_preparation_authorized": True,
        "local_package_validation_authorized": True,
        "final_exact_results_and_package_approval_required": True,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "population_inference_allowed": False,
        "archive_wide_claim_allowed": False,
        "redistribution_allowed": False,
        "publication_allowed": False,
        "release_allowed": False,
        "dataset_publication_allowed": False,
        "paper_updates_allowed": False,
        "arxiv_submission_allowed": False,
        "external_action_allowed": False,
    }
    auth_path = root / "meta/auth.json"
    _json(auth_path, auth)
    head = _commit(root, "auth")
    for name, value in (
        ("PLAN_PATH", plan_path),
        ("PLAN_SHA256", plan_pin["sha256"]),
        ("PLAN_COMMIT", plan_commit),
        ("APPROVAL_PATH", approval_path),
        ("APPROVAL_SHA256", approval_pin["sha256"]),
        ("APPROVAL_COMMIT", approval_commit),
        ("AUTHORIZATION_PATH", "meta/auth.json"),
    ):
        monkeypatch.setattr(execution, name, value)
    if provenance_bridge:
        monkeypatch.setattr(execution, "REQUEST_35076_CONTEXT_SOURCE", context2)
    permission = execution.verify_pre_materialization(
        repository_root=root,
        authorization_path=auth_path,
        expected_authorization_sha256=_sha(auth_path),
        expected_repository_commit=head,
    )
    return root, auth_path, head, permission


def test_exact_metadata_driven_builder_and_post_lock_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, permission = _fixture(tmp_path, monkeypatch)
    lock = execution.materialize_contexts(permission)
    assert lock.stage == "S3_ANALYST_EXECUTION"
    manifest = json.loads((lock.workspace / "context-manifest.locked.json").read_text())
    validation = validate_json_schema(
        lock.workspace / "context-manifest.locked.json",
        ROOT / "schemas/json/bounded-pilot-context-manifest-v0.2.schema.json",
    )
    assert not validation.errors, validation.errors
    assert [s["segment_id"] for s in manifest["segments"]] == [
        "block-0",
        "block-1",
        "block-2",
        "block-3",
        "attachment-000.txt",
        "attachment-001.txt",
        "attachment-002.txt",
        "block-0",
    ]
    assert (lock.workspace / "analyst-a.context.txt").read_bytes() == (
        lock.workspace / "analyst-b.context.txt"
    ).read_bytes()
    assert manifest["reconciliation_allowed"] is False


@pytest.mark.parametrize("mutation", ["dirty", "source", "approval", "unexpected"])
def test_all_stages_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root, _, _, permission = _fixture(tmp_path, monkeypatch)
    if mutation == "dirty":
        (root / "dirty").write_text("x")
    elif mutation == "source":
        (permission.source_roots["derived_attachments"] / "attachment-000.txt").write_text("drift")
    elif mutation == "approval":
        monkeypatch.setattr(execution, "APPROVAL_SHA256", "0" * 64)
    else:
        execution.materialize_contexts(permission)
        (permission.workspace / "extra").write_text("x")
        with pytest.raises(ValueError, match="inventory"):
            execution.verify_materialized_contexts(permission)
        return
    with pytest.raises(ValueError, match=r"worktree|source|approval|artifact"):
        execution.materialize_contexts(permission)


def test_rejects_symlinked_source_and_permission_forgery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, permission = _fixture(tmp_path, monkeypatch)
    page = permission.source_roots["request_11872_source"] / "content/page.html"
    real = page.with_name("real.html")
    page.replace(real)
    page.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        execution.materialize_contexts(permission)
    with pytest.raises(ValueError, match="cannot be constructed"):
        execution.StagePermission(_token=object())


def test_verified_reextraction_root_can_bind_exact_companion_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, permission = _fixture(tmp_path, monkeypatch, provenance_bridge=True)
    assert "request_35076_context_source" in permission.source_roots
    assert execution.materialize_contexts(permission).stage == "S3_ANALYST_EXECUTION"
