import json
import shutil
from hashlib import sha256
from pathlib import Path
from subprocess import run

import pytest

from foi_o_nz.analyst_packet_verification import (
    verify_analyst_execution_packet,
    verify_fixture_role_authorization_request,
)
from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_role_authorization_request import main as build_request

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
REQUEST = PACKET / "role-authorization-request.pending.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in {"assertion_status", "confidence"} or _contains_forbidden_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def test_pending_request_is_schema_valid_and_fail_closed() -> None:
    assert not validate_json_schema(
        REQUEST, ROOT / "schemas/json/fixture-role-authorization-request.schema.json"
    ).errors
    request = _load(REQUEST)
    assert request["promotion_commit"] == "fe875ab254ff914b18143cfe08fee202b8b532b1"
    assert request["approved_input_readiness"] == {
        "path": "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
        "sha256": "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e",
    }
    assert request["human_approval_present"] is False
    assert request["approved_by"] is None
    assert request["approved_at"] is None
    assert request["execution_authorization_present"] is False
    assert request["execution_allowed"] is False
    assert "execution" in request["prohibited_actions"]


def test_role_records_are_truthful_distinct_and_prompt_pinned() -> None:
    request = _load(REQUEST)
    expected = {
        "orchestrator": ("/root/fixture_stream_ready", "orchestrator_non_labeling", False),
        "analyst_a": ("/root/fixture_analyst_a_ready", "analyst", True),
        "analyst_b": ("/root/fixture_analyst_b_ready", "analyst", True),
        "reconciler": ("/root/fixture_reconciler_ready", "reconciler", False),
    }
    locators = []
    actors = []
    for name, (locator, role, may_label) in expected.items():
        pin = request["role_provenance"][name]  # type: ignore[index]
        path = ROOT / pin["path"]
        assert _digest(path) == pin["sha256"]
        record = _load(path)
        assert record["canonical_session_locator"] == locator
        assert record["role"] == role
        assert record["may_label"] is may_label
        assert record["immutable_session_uuid_available"] is False
        assert record["immutable_session_uuid"] is None
        assert record["runtime"] == {
            "provider_family": None,
            "model_runtime_family": None,
            "exact_snapshot_available": False,
            "exact_snapshot": None,
        }
        assert record["handshake_completed"] is False
        assert record["execution_allowed"] is False
        prompt_pin = record["future_execution_prompt"]
        assert _digest(ROOT / prompt_pin["path"]) == prompt_pin["sha256"]
        locators.append(locator)
        actors.append(record["actor_id"])
    assert len(set(locators)) == 4
    assert len(set(actors)) == 4


def test_context_manifest_is_exact_redacted_eleven_unit_presentation() -> None:
    manifest = _load(PACKET / "context-presentation.pending.json")
    contexts = manifest["contexts"]
    assert manifest["status"] == "prepared_not_presented"
    assert manifest["unit_count"] == len(contexts) == 11
    assert manifest["execution_allowed"] is False
    assert not _contains_forbidden_key(contexts)
    for item in contexts:
        encoded = json.dumps(
            item["presented_context"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert sha256(encoded).hexdigest() == item["context_sha256"]


def test_promoted_readiness_pin_is_exactly_anchored_to_declared_commit() -> None:
    readiness = PACKET / "input-readiness.approved.json"
    assert _digest(readiness) == "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e"
    committed = run(
        [
            "git",
            "show",
            "fe875ab254ff914b18143cfe08fee202b8b532b1:examples/v2/analyst-fixture-packet/input-readiness.approved.json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert committed == readiness.read_bytes()


def test_builder_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    packet = root / "examples/v2/analyst-fixture-packet"
    packet.mkdir(parents=True)
    for relative in [
        "examples/process-mining-events.fixture.jsonl",
        "examples/event-timeline.small.json",
    ]:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    build_request(packet, repository_root=root)
    generated = sorted(path.relative_to(packet) for path in packet.rglob("*") if path.is_file())
    tracked = [
        Path("context-presentation.pending.json"),
        Path("role-authorization-request.pending.json"),
        Path("role-isolation-plan.pending.json"),
        *[
            Path(f"role-provenance.{name}.pending.json")
            for name in ("orchestrator", "analyst_a", "analyst_b", "reconciler")
        ],
        *[path.relative_to(PACKET) for path in (PACKET / "prompts").glob("*.txt")],
    ]
    assert generated == sorted(tracked)
    for relative in generated:
        assert (packet / relative).read_bytes() == (PACKET / relative).read_bytes()


def test_schema_rejects_any_execution_or_approval_claim(tmp_path: Path) -> None:
    request = _load(REQUEST)
    request["execution_allowed"] = True
    request["human_approval_present"] = True
    changed = tmp_path / "request.json"
    changed.write_text(json.dumps(request), encoding="utf-8")
    assert validate_json_schema(
        changed, ROOT / "schemas/json/fixture-role-authorization-request.schema.json"
    ).errors


def _committed_preparation(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(root)], check=True)
    packet = root / "examples/v2/analyst-fixture-packet"
    build_request(packet, repository_root=root)
    run(["git", "add", "examples/v2/analyst-fixture-packet"], cwd=root, check=True)
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
                "preparation",
            ],
            cwd=root,
            check=True,
        )
    elif staged.returncode != 0:
        staged.check_returncode()
    commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    request = packet / "role-authorization-request.pending.json"
    return root, request, _digest(request), commit


def test_public_pending_request_verifier_accepts_exact_committed_preparation(
    tmp_path: Path,
) -> None:
    root, request, request_hash, commit = _committed_preparation(tmp_path)
    result = verify_fixture_role_authorization_request(
        repository_root=root,
        request_path=request,
        expected_request_sha256=request_hash,
        expected_preparation_repository_commit=commit,
        expected_base_repository_commit="948d392df7fbbf49ea9b33646a0bdbd845505811",
        expected_promotion_repository_commit="fe875ab254ff914b18143cfe08fee202b8b532b1",
    )
    assert (result.role_count, result.context_count, result.execution_allowed) == (4, 11, False)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("duplicate_locator", "role or prompt alignment mismatch"),
        ("swap_prompt", "role or prompt alignment mismatch"),
        ("actor_id", "role or prompt alignment mismatch"),
        ("handshake_content", "not the canonical governed prompt"),
        ("orchestrator_prompt_content", "not the canonical governed prompt"),
        ("analyst_a_prompt_content", "not the canonical governed prompt"),
        ("analyst_b_prompt_content", "not the canonical governed prompt"),
        ("reconciler_prompt_content", "not the canonical governed prompt"),
        ("uuid", "immutable_session_uuid"),
        ("provider", "provider_family"),
        ("context_order", "exact ordered redacted census"),
        ("context_key", "exact ordered redacted census"),
        ("handshake", "handshake_completed"),
        ("execution", "execution_allowed"),
    ],
)
def test_public_verifier_rejects_rehashed_semantic_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root, request_path, _, _ = _committed_preparation(tmp_path)
    request = _load(request_path)
    if mutation in {
        "duplicate_locator",
        "swap_prompt",
        "actor_id",
        "uuid",
        "provider",
        "handshake",
    }:
        role_path = root / request["role_provenance"]["analyst_a"]["path"]  # type: ignore[index]
        role = _load(role_path)
        if mutation == "duplicate_locator":
            role["canonical_session_locator"] = "/root/fixture_analyst_b_ready"
        elif mutation == "swap_prompt":
            role["future_execution_prompt"] = request["future_execution_prompts"]["analyst_b"]  # type: ignore[index]
        elif mutation == "actor_id":
            role["actor_id"] = "agent:substituted-analyst"
        elif mutation == "uuid":
            role["immutable_session_uuid_available"] = True
            role["immutable_session_uuid"] = "invented"
        elif mutation == "provider":
            role["runtime"]["provider_family"] = "invented"  # type: ignore[index]
        else:
            role["handshake_completed"] = True
        role_path.write_text(json.dumps(role, indent=2, sort_keys=True) + "\n")
        request["role_provenance"]["analyst_a"]["sha256"] = _digest(role_path)  # type: ignore[index]
    elif mutation == "handshake_content":
        prompt_path = root / request["handshake_prompt"]["path"]  # type: ignore[index]
        prompt_path.write_text("substituted handshake\n", encoding="utf-8")
        request["handshake_prompt"]["sha256"] = _digest(prompt_path)  # type: ignore[index]
        for _name, pin in request["role_provenance"].items():  # type: ignore[union-attr]
            role_path = root / pin["path"]
            role = _load(role_path)
            role["handshake_prompt"] = request["handshake_prompt"]
            role_path.write_text(json.dumps(role, indent=2, sort_keys=True) + "\n")
            pin["sha256"] = _digest(role_path)
    elif mutation.endswith("_prompt_content"):
        name = mutation.removesuffix("_prompt_content")
        prompt_pin = request["future_execution_prompts"][name]  # type: ignore[index]
        prompt_path = root / prompt_pin["path"]
        prompt_path.write_text(f"substituted {name} prompt\n", encoding="utf-8")
        prompt_pin["sha256"] = _digest(prompt_path)
        role_pin = request["role_provenance"][name]  # type: ignore[index]
        role_path = root / role_pin["path"]
        role = _load(role_path)
        role["future_execution_prompt"] = prompt_pin
        role_path.write_text(json.dumps(role, indent=2, sort_keys=True) + "\n")
        role_pin["sha256"] = _digest(role_path)
    elif mutation in {"context_order", "context_key"}:
        context_path = root / request["context_presentation"]["path"]  # type: ignore[index]
        context = _load(context_path)
        if mutation == "context_order":
            context["contexts"][0], context["contexts"][1] = (
                context["contexts"][1],
                context["contexts"][0],
            )  # type: ignore[index]
        else:
            context["contexts"][0]["presented_context"]["confidence"] = 1  # type: ignore[index]
        context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n")
        request["context_presentation"]["sha256"] = _digest(context_path)  # type: ignore[index]
    else:
        request["execution_allowed"] = True
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
    run(["git", "add", "."], cwd=root, check=True)
    run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "mutation",
        ],
        cwd=root,
        check=True,
    )
    commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    with pytest.raises(ValueError, match=message):
        verify_fixture_role_authorization_request(
            repository_root=root,
            request_path=request_path,
            expected_request_sha256=_digest(request_path),
            expected_preparation_repository_commit=commit,
            expected_base_repository_commit="948d392df7fbbf49ea9b33646a0bdbd845505811",
            expected_promotion_repository_commit="fe875ab254ff914b18143cfe08fee202b8b532b1",
        )


def test_execution_verifier_explicitly_rejects_pending_request(tmp_path: Path) -> None:
    root, request, request_hash, commit = _committed_preparation(tmp_path)
    with pytest.raises(ValueError, match="pending role authorization request cannot be used"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=request,
            expected_authorization_sha256=request_hash,
            expected_repository_commit=commit,
        )
