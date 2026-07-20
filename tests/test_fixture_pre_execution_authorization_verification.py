import json
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

import pytest

from foi_o_nz.analyst_packet_verification import (
    verify_analyst_execution_packet,
    verify_fixture_pre_execution_authorization,
)
from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_executable_authorization import main as build_authorization

ROOT = Path(__file__).parents[1]
PACKET_RELATIVE = Path("examples/v2/analyst-fixture-packet")
BASE_COMMIT = "948d392df7fbbf49ea9b33646a0bdbd845505811"
PROMOTION_COMMIT = "fe875ab254ff914b18143cfe08fee202b8b532b1"
PREPARATION_COMMIT = "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
REQUEST_SHA256 = "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"
HANDSHAKE_AUTH_COMMIT = "393991ea0cfdaf9f016108bf74edae94b80f042a"
HANDSHAKE_AUTH_SHA256 = "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f"
EVIDENCE_COMMIT = "21c6db101e3afee4de96d8e2d924331eb76d9dbe"
EVIDENCE_SHA256 = "709625146544dd0abad8af22acb718e7c68cabf0f41ac59cb310e30107e3cb6b"
CANDIDATE_COMMIT = "5cbfbe80beee96c67cdcabbf352b97d5dffd6cbf"
CANDIDATE_SHA256 = "a1aab22f6f7870497f639e871cc4aa13d209ca35b72f8da89559bcf9940dab1d"


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _commit(root: Path, message: str) -> str:
    run(["git", "add", "."], cwd=root, check=True)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False)
    if staged.returncode == 1:
        run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                message,
            ],
            cwd=root,
            check=True,
        )
    elif staged.returncode != 0:
        staged.check_returncode()
    return run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _committed_authorization(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(root)], check=True)
    packet = root / PACKET_RELATIVE
    build_authorization(packet, repository_root=root)
    authorization = packet / "execution-authorization.v0.2.pending-verification.json"
    commit = _commit(root, "derive executable fixture authorization")
    return root, authorization, _digest(authorization), commit


def _verify(root: Path, authorization: Path, digest: str, commit: str) -> None:
    result = verify_fixture_pre_execution_authorization(
        repository_root=root,
        authorization_path=authorization,
        expected_authorization_sha256=digest,
        expected_repository_commit=commit,
        expected_candidate_sha256=CANDIDATE_SHA256,
        expected_candidate_repository_commit=CANDIDATE_COMMIT,
        expected_handshake_evidence_sha256=EVIDENCE_SHA256,
        expected_handshake_evidence_repository_commit=EVIDENCE_COMMIT,
        expected_handshake_authorization_sha256=HANDSHAKE_AUTH_SHA256,
        expected_handshake_authorization_repository_commit=HANDSHAKE_AUTH_COMMIT,
        expected_request_sha256=REQUEST_SHA256,
        expected_preparation_repository_commit=PREPARATION_COMMIT,
        expected_base_repository_commit=BASE_COMMIT,
        expected_promotion_repository_commit=PROMOTION_COMMIT,
    )
    assert result.role_count == 4
    assert result.context_presentation_allowed is True
    assert result.analysis_execution_allowed is True
    assert result.reconciliation_allowed is False
    assert result.execution_allowed is True


def test_public_verifier_accepts_exact_committed_wrapper_only(tmp_path: Path) -> None:
    root, authorization, digest, commit = _committed_authorization(tmp_path)
    _verify(root, authorization, digest, commit)


def test_public_verifier_rejects_incorrect_external_wrapper_sha256(tmp_path: Path) -> None:
    root, authorization, _, commit = _committed_authorization(tmp_path)
    with pytest.raises(ValueError, match="authorization SHA-256 mismatch"):
        _verify(root, authorization, "0" * 64, commit)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("approval_text", "candidate_approval"),
        ("candidate_pin", "fixture pre-execution candidate pin mismatch"),
        ("inherited_pin", "differs from candidate"),
        ("orchestrator_labels", "fixture pre-execution role conditions are not exact"),
        ("wrapper_effective", "fixture_pre_execution_authorization"),
        ("context_allowed", "fixture_pre_execution_authorization"),
        ("analysis_allowed", "fixture_pre_execution_authorization"),
        ("reconciliation_allowed", "fixture_pre_execution_authorization"),
        ("execution_allowed", "fixture_pre_execution_authorization"),
        ("prohibition_order", "prohibitions are not exact"),
    ],
)
def test_public_verifier_rejects_rehashed_wrapper_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root, authorization_path, _, _ = _committed_authorization(tmp_path)
    document = _load(authorization_path)
    if mutation == "approval_text":
        approval_path = root / document["candidate_approval"]["path"]
        approval = _load(approval_path)
        approval["approval_statement"] = "substituted approval"
        approval["approval_statement_sha256"] = sha256(b"substituted approval").hexdigest()
        _write(approval_path, approval)
        document["candidate_approval"]["sha256"] = _digest(approval_path)
    elif mutation == "candidate_pin":
        document["derived_from_candidate"]["sha256"] = "0" * 64
    elif mutation == "inherited_pin":
        document["approved_input_readiness"]["sha256"] = "0" * 64
    elif mutation == "orchestrator_labels":
        document["role_execution_conditions"]["orchestrator"]["may_label"] = True
    elif mutation == "wrapper_effective":
        document["authorization_effective"] = True
    elif mutation == "context_allowed":
        document["context_presentation_allowed"] = True
    elif mutation == "analysis_allowed":
        document["analysis_execution_allowed"] = True
    elif mutation == "reconciliation_allowed":
        document["reconciliation_allowed"] = True
    elif mutation == "execution_allowed":
        document["execution_allowed"] = True
    else:
        document["prohibited_actions"][0], document["prohibited_actions"][1] = (
            document["prohibited_actions"][1],
            document["prohibited_actions"][0],
        )
    _write(authorization_path, document)
    commit = _commit(root, f"mutation {mutation}")
    with pytest.raises(ValueError, match=message):
        _verify(root, authorization_path, _digest(authorization_path), commit)


def test_public_verifier_rejects_relocated_dirty_and_untracked_wrapper(tmp_path: Path) -> None:
    root, authorization, _, commit = _committed_authorization(tmp_path)
    relocated = root / "relocated-execution-authorization.json"
    relocated.write_bytes(authorization.read_bytes())
    with pytest.raises(ValueError, match="authorization path is not canonical"):
        _verify(root, relocated, _digest(relocated), commit)
    authorization.write_bytes(authorization.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differs from anchored commit"):
        _verify(root, authorization, _digest(authorization), commit)


@pytest.mark.parametrize(
    "readiness_path",
    [
        "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
        "copied-fixtures/input-readiness.approved.json",
    ],
)
def test_schema_valid_legacy_three_role_shape_is_retired_even_after_relocation(
    tmp_path: Path, readiness_path: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    artifact_names = (
        "approved_input_readiness",
        "protocol",
        "source_population",
        "codebook",
        "sampling_configuration",
        "unit_manifest",
        "duplicate_cluster_registry",
        "redaction_manifest",
        "local_rights_review",
    )
    artifacts = {
        name: {"path": f"fixtures/{name}.json", "sha256": "a" * 64, "state": "locked"}
        for name in artifact_names
    }
    artifacts["approved_input_readiness"] = {
        "path": readiness_path,
        "sha256": "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e",
        "state": "locked",
    }
    runtime = {"provider": "codex", "model": "recorded", "prompt_sha256": "a" * 64}
    payload = {
        "schema_version": "foi-o.analyst-execution-authorization.v0.2.0",
        "authorization_id": "legacy-fixture-shape",
        "status": "approved_local_agent_analysis",
        "execution_allowed": True,
        "local_only": True,
        "artifacts": artifacts,
        "analysts": [
            {
                "actor_id": "agent:analyst-a",
                "actor_class": "automated_agent",
                "role": "analyst",
                "runtime": {**runtime, "session_id": "a"},
            },
            {
                "actor_id": "agent:analyst-b",
                "actor_class": "automated_agent",
                "role": "analyst",
                "runtime": {**runtime, "session_id": "b"},
            },
        ],
        "reconciler": {
            "actor_id": "agent:reconciler",
            "actor_class": "automated_agent",
            "role": "reconciler",
            "runtime": {**runtime, "session_id": "r"},
        },
        "approved_by": "human:test",
        "approved_at": "2026-07-19T00:00:00Z",
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "prohibited_actions": [
            "redistribution",
            "publication",
            "training",
            "fine_tuning",
            "release",
            "dataset_publication",
            "gold_promotion",
            "legal_certification",
            "paper_update",
        ],
    }
    authorization = root / "legacy.json"
    _write(authorization, payload)
    assert not validate_json_schema(
        authorization, ROOT / "schemas/json/analyst-execution-authorization.v0.2.schema.json"
    ).errors
    with pytest.raises(ValueError, match="legacy three-role analyst authorization is retired"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=authorization,
            expected_authorization_sha256=_digest(authorization),
            expected_repository_commit="0" * 40,
        )
