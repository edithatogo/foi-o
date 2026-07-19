import json
from hashlib import sha256
from pathlib import Path
from subprocess import run
from typing import Any

import pytest

from foi_o_nz.analyst_packet_verification import (
    verify_analyst_execution_packet,
    verify_fixture_runtime_handshake_evidence,
)
from scripts.build_fixture_runtime_handshake_evidence import main as build_evidence

ROOT = Path(__file__).parents[1]
PACKET_RELATIVE = Path("examples/v2/analyst-fixture-packet")
BASE_COMMIT = "948d392df7fbbf49ea9b33646a0bdbd845505811"
PROMOTION_COMMIT = "fe875ab254ff914b18143cfe08fee202b8b532b1"
PREPARATION_COMMIT = "91013a0f69d3a376ec749bbad83902e7ac4dd2a7"
REQUEST_SHA256 = "232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c"
AUTHORIZATION_COMMIT = "393991ea0cfdaf9f016108bf74edae94b80f042a"
AUTHORIZATION_SHA256 = "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f"


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


def _committed_bundle(tmp_path: Path) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(root)], check=True)
    packet = root / PACKET_RELATIVE
    build_evidence(packet, repository_root=root)
    bundle = packet / "runtime-handshake-readiness.locked.json"
    commit = _commit(root, "lock runtime handshake evidence")
    return root, bundle, _digest(bundle), commit


def _verify(root: Path, bundle: Path, digest: str, commit: str) -> None:
    result = verify_fixture_runtime_handshake_evidence(
        repository_root=root,
        bundle_path=bundle,
        expected_bundle_sha256=digest,
        expected_repository_commit=commit,
        expected_authorization_sha256=AUTHORIZATION_SHA256,
        expected_authorization_repository_commit=AUTHORIZATION_COMMIT,
        expected_request_sha256=REQUEST_SHA256,
        expected_preparation_repository_commit=PREPARATION_COMMIT,
        expected_base_repository_commit=BASE_COMMIT,
        expected_promotion_repository_commit=PROMOTION_COMMIT,
    )
    assert result.role_count == 4
    assert result.runtime_handshakes_complete is True
    assert result.execution_allowed is False


def test_public_verifier_accepts_exact_committed_four_role_bundle(tmp_path: Path) -> None:
    root, bundle, digest, commit = _committed_bundle(tmp_path)
    _verify(root, bundle, digest, commit)


def test_public_verifier_rejects_incorrect_external_bundle_sha256(tmp_path: Path) -> None:
    root, bundle, _, commit = _committed_bundle(tmp_path)
    with pytest.raises(ValueError, match="runtime handshake evidence bundle SHA-256 mismatch"):
        _verify(root, bundle, "0" * 64, commit)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("raw_reply", "raw reply mismatch"),
        ("normalized_runtime", "runtime_handshake_evidence.analyst_a"),
        ("duplicate_locator", "provenance mismatch"),
        ("swapped_role", "provenance mismatch"),
        ("available_null", "runtime_handshake_evidence.analyst_a"),
        ("reply_time", "runtime_handshake_evidence.analyst_a"),
        ("delivery_time", "runtime_handshake_evidence.analyst_a"),
        ("context_field", "runtime_handshake_evidence.analyst_a"),
        ("context_delivered", "runtime_handshake_evidence.analyst_a"),
        ("label_delivered", "runtime_handshake_evidence.analyst_a"),
        ("peer_output_delivered", "runtime_handshake_evidence.analyst_a"),
        ("analysis_allowed", "runtime_handshake_evidence.analyst_a"),
        ("reconciliation_allowed", "runtime_handshake_evidence.analyst_a"),
        ("evidence_id", "provenance mismatch"),
        ("record_relocation", "record path is not canonical"),
        ("raw_relocation", "raw reply path is not canonical"),
        ("missing_record", "runtime_handshake_readiness.evidence_records"),
        ("unlocked", "runtime_handshake_readiness.runtime_handshakes_complete"),
    ],
)
def test_public_verifier_rejects_rehashed_semantic_mutations(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root, bundle_path, _, _ = _committed_bundle(tmp_path)
    bundle = _load(bundle_path)
    if mutation in {
        "raw_reply",
        "normalized_runtime",
        "duplicate_locator",
        "swapped_role",
        "available_null",
        "reply_time",
        "delivery_time",
        "context_field",
        "context_delivered",
        "label_delivered",
        "peer_output_delivered",
        "analysis_allowed",
        "reconciliation_allowed",
        "evidence_id",
        "record_relocation",
        "raw_relocation",
    }:
        record_pin = bundle["evidence_records"]["analyst_a"]  # type: ignore[index]
        record_path = root / record_pin["path"]
        record = _load(record_path)
        if mutation == "raw_reply":
            raw_path = root / record["raw_reply"]["path"]  # type: ignore[index]
            raw_path.write_text("substituted but rehashed reply\n", encoding="utf-8")
            record["raw_reply"]["sha256"] = _digest(raw_path)  # type: ignore[index]
            record["raw_reply_text"] = raw_path.read_text(encoding="utf-8")
        elif mutation == "normalized_runtime":
            record["normalized_runtime_family"] = "invented runtime"
        elif mutation == "duplicate_locator":
            record["canonical_session_locator"] = "/root/fixture_analyst_b_ready"
        elif mutation == "swapped_role":
            record["actor_id"] = "agent:analyst-fixture-b"
        elif mutation == "available_null":
            record["exact_model_snapshot_available"] = True
        elif mutation == "reply_time":
            record["reply_time_available"] = True
        elif mutation == "delivery_time":
            record["delivered_at"] = "2026-07-19T10:00:00+10:00"
        elif mutation == "context_field":
            record["contexts"] = []
        elif mutation == "context_delivered":
            record["fixture_context_delivered_with_handshake"] = True
        elif mutation == "label_delivered":
            record["label_material_delivered_with_handshake"] = True
        elif mutation == "peer_output_delivered":
            record["peer_output_delivered_with_handshake"] = True
        elif mutation == "analysis_allowed":
            record["analysis_execution_allowed"] = True
        elif mutation == "reconciliation_allowed":
            record["reconciliation_allowed"] = True
        elif mutation == "evidence_id":
            record["evidence_id"] = "substituted-evidence-id"
        elif mutation == "record_relocation":
            relocated = record_path.with_name("relocated-evidence.analyst_a.json")
            _write(relocated, record)
            record_pin["path"] = relocated.relative_to(root).as_posix()
            record_pin["sha256"] = _digest(relocated)
            record_path = relocated
        else:
            raw_path = root / record["raw_reply"]["path"]
            relocated = raw_path.with_name("relocated-reply.analyst_a.txt")
            relocated.write_bytes(raw_path.read_bytes())
            record["raw_reply"]["path"] = relocated.relative_to(root).as_posix()
            record["raw_reply"]["sha256"] = _digest(relocated)
        _write(record_path, record)
        record_pin["sha256"] = _digest(record_path)
    elif mutation == "missing_record":
        bundle["evidence_records"].pop("reconciler")  # type: ignore[union-attr]
    else:
        bundle["runtime_handshakes_complete"] = False
    _write(bundle_path, bundle)
    commit = _commit(root, f"mutation {mutation}")
    with pytest.raises(ValueError, match=message):
        _verify(root, bundle_path, _digest(bundle_path), commit)


def test_public_verifier_rejects_wrong_authorization_checkpoint(tmp_path: Path) -> None:
    root, bundle, digest, commit = _committed_bundle(tmp_path)
    with pytest.raises(ValueError, match="runtime handshake authorization pin mismatch"):
        verify_fixture_runtime_handshake_evidence(
            repository_root=root,
            bundle_path=bundle,
            expected_bundle_sha256=digest,
            expected_repository_commit=commit,
            expected_authorization_sha256="0" * 64,
            expected_authorization_repository_commit=AUTHORIZATION_COMMIT,
            expected_request_sha256=REQUEST_SHA256,
            expected_preparation_repository_commit=PREPARATION_COMMIT,
            expected_base_repository_commit=BASE_COMMIT,
            expected_promotion_repository_commit=PROMOTION_COMMIT,
        )


def test_public_verifier_rejects_dirty_and_untracked_evidence(tmp_path: Path) -> None:
    root, bundle, _, commit = _committed_bundle(tmp_path)
    bundle.write_bytes(bundle.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="differs from anchored commit"):
        _verify(root, bundle, _digest(bundle), commit)

    untracked = root / "untracked-runtime-handshake-readiness.json"
    untracked.write_bytes(bundle.read_bytes()[:-1])
    with pytest.raises(ValueError, match="bundle path is not canonical"):
        _verify(root, untracked, _digest(untracked), commit)


def test_handshake_bundle_is_explicitly_rejected_by_analysis_verifier(tmp_path: Path) -> None:
    root, bundle, digest, commit = _committed_bundle(tmp_path)
    with pytest.raises(ValueError, match="runtime handshake evidence bundle cannot be used"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=bundle,
            expected_authorization_sha256=digest,
            expected_repository_commit=commit,
        )

    document = _load(bundle)
    record_path = root / document["evidence_records"]["analyst_a"]["path"]
    with pytest.raises(ValueError, match="runtime handshake evidence record cannot be used"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=record_path,
            expected_authorization_sha256=_digest(record_path),
            expected_repository_commit=commit,
        )
