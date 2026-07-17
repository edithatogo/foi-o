import json
import shutil
from hashlib import sha256
from pathlib import Path
from subprocess import run

import pytest

from foi_o_nz.analyst_packet_verification import verify_approved_fixture_inputs
from foi_o_nz.validation import validate_json_schema
from scripts.promote_analyst_fixture_inputs import main as promote_inputs

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
SCHEMAS = ROOT / "schemas/json"
CANDIDATE = [
    "source-population.json",
    "codebook.json",
    "sampling-configuration.json",
    "unit-manifest.json",
    "cluster-registry.json",
    "redaction-manifest.json",
    "local-rights-review.pending.json",
    "readiness.json",
]
APPROVED_SCHEMAS = {
    "input-approval.approved.json": "analyst-fixture-input-approval.schema.json",
    "local-rights-review.approved.json": "analyst-approved-local-rights-review.schema.json",
    "codebook.approved.json": "analyst-approved-fixture-codebook.schema.json",
    "sampling-configuration.approved.json": "analyst-approved-sampling-configuration.schema.json",
    "unit-manifest.rights-approved.json": "analyst-fixture-unit-manifest.schema.json",
    "cluster-registry.rights-approved.json": "analyst-fixture-cluster-registry.schema.json",
    "input-readiness.approved.json": "analyst-fixture-approved-input-readiness.schema.json",
}


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _candidate_copy(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    packet = root / "examples/v2/analyst-fixture-packet"
    packet.mkdir(parents=True)
    protocol = root / "docs/42-v2-analyst-execution-protocol.md"
    protocol.parent.mkdir()
    shutil.copy2(ROOT / "docs/42-v2-analyst-execution-protocol.md", protocol)
    for name in CANDIDATE:
        shutil.copy2(PACKET / name, packet / name)
    return packet


def _committed_candidate(tmp_path: Path) -> tuple[Path, Path, str]:
    packet = _candidate_copy(tmp_path)
    root = packet.parents[2]
    for relative in [
        "examples/process-mining-events.fixture.jsonl",
        "examples/event-timeline.small.json",
        "LICENSE.md",
    ]:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    run(["git", "init", "-q"], cwd=root, check=True)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
    run(["git", "add", "."], cwd=root, check=True)
    run(["git", "commit", "-qm", "candidate"], cwd=root, check=True)
    base_commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return root, packet, base_commit


def _commit_promotion(root: Path, packet: Path, base_commit: str) -> str:
    promote_inputs(packet, packet, repository_root=root, base_repository_commit=base_commit)
    run(["git", "add", "."], cwd=root, check=True)
    run(["git", "commit", "-qm", "promotion"], cwd=root, check=True)
    return run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_approved_input_promotion_is_stable_valid_and_preserves_candidates(tmp_path: Path) -> None:
    packet = _candidate_copy(tmp_path)
    before = {name: (packet / name).read_bytes() for name in CANDIDATE}
    promote_inputs(packet, packet)
    assert {name: (packet / name).read_bytes() for name in CANDIDATE} == before
    for name, schema in APPROVED_SCHEMAS.items():
        assert (packet / name).read_bytes() == (PACKET / name).read_bytes()
        assert not validate_json_schema(packet / name, SCHEMAS / schema).errors


def test_approved_inputs_verify_but_never_enable_execution(tmp_path: Path) -> None:
    root, packet, base_commit = _committed_candidate(tmp_path)
    promotion_commit = _commit_promotion(root, packet, base_commit)
    approval = packet / "input-approval.approved.json"
    readiness = packet / "input-readiness.approved.json"
    result = verify_approved_fixture_inputs(
        repository_root=root,
        packet_dir=packet,
        expected_approval_sha256=_digest(approval),
        expected_approved_input_readiness_sha256=_digest(readiness),
        expected_base_repository_commit=base_commit,
        expected_promotion_repository_commit=promotion_commit,
    )
    assert result.unit_count == 11
    assert result.execution_allowed is False
    assert json.loads(readiness.read_text())["execution_allowed"] is False
    assert not (packet / "authorization.approved.json").exists()


def test_verifier_rejects_untracked_required_promotion_artifact(tmp_path: Path) -> None:
    root, packet, base_commit = _committed_candidate(tmp_path)
    promote_inputs(packet, packet, repository_root=root, base_repository_commit=base_commit)
    readiness = packet / "input-readiness.approved.json"

    with pytest.raises(ValueError, match="not tracked at anchored commit"):
        verify_approved_fixture_inputs(
            repository_root=root,
            packet_dir=packet,
            expected_approval_sha256=_digest(packet / "input-approval.approved.json"),
            expected_approved_input_readiness_sha256=_digest(readiness),
            expected_base_repository_commit=base_commit,
            expected_promotion_repository_commit=base_commit,
        )


def test_verifier_rejects_wrong_historical_base_commit(tmp_path: Path) -> None:
    root, packet, base_commit = _committed_candidate(tmp_path)
    promote_inputs(packet, packet, repository_root=root, base_repository_commit=base_commit)
    nonexistent_commit = "0" * 40
    approval_path = packet / "input-approval.approved.json"
    approval = json.loads(approval_path.read_text())
    approval["approved_repository_commit"] = nonexistent_commit
    approval_path.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n")
    readiness_path = packet / "input-readiness.approved.json"
    readiness = json.loads(readiness_path.read_text())
    readiness["base_readiness"]["repository_commit"] = nonexistent_commit
    readiness["approved_artifacts"]["input_approval"]["sha256"] = _digest(approval_path)
    readiness_path.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    run(["git", "add", "."], cwd=root, check=True)
    run(["git", "commit", "-qm", "promotion with wrong base anchor"], cwd=root, check=True)
    promotion_commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()

    with pytest.raises(ValueError, match="not present at base commit"):
        verify_approved_fixture_inputs(
            repository_root=root,
            packet_dir=packet,
            expected_approval_sha256=_digest(approval_path),
            expected_approved_input_readiness_sha256=_digest(readiness_path),
            expected_base_repository_commit=nonexistent_commit,
            expected_promotion_repository_commit=promotion_commit,
        )


def test_verifier_rejects_wrong_final_promotion_commit(tmp_path: Path) -> None:
    root, packet, base_commit = _committed_candidate(tmp_path)
    _commit_promotion(root, packet, base_commit)
    readiness = packet / "input-readiness.approved.json"

    with pytest.raises(ValueError, match="repository commit mismatch"):
        verify_approved_fixture_inputs(
            repository_root=root,
            packet_dir=packet,
            expected_approval_sha256=_digest(packet / "input-approval.approved.json"),
            expected_approved_input_readiness_sha256=_digest(readiness),
            expected_base_repository_commit=base_commit,
            expected_promotion_repository_commit=base_commit,
        )


def test_recorded_at_is_not_claimed_as_approval_time() -> None:
    approval = json.loads((PACKET / "input-approval.approved.json").read_text())
    assert approval["approved_on"] == "2026-07-17"
    assert approval["recorded_at"] == "2026-07-17T23:04:58+10:00"
    assert approval["recording_note"] == (
        "recorded_at is provenance only and is not claimed as approval time"
    )
    assert "approved_at" not in approval


def test_approved_input_schema_rejects_execution(tmp_path: Path) -> None:
    source = PACKET / "input-readiness.approved.json"
    payload = json.loads(source.read_text())
    payload["execution_allowed"] = True
    changed = tmp_path / source.name
    changed.write_text(json.dumps(payload))
    assert validate_json_schema(
        changed, SCHEMAS / "analyst-fixture-approved-input-readiness.schema.json"
    ).errors


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        ("codebook.approved.json", "approved codebook transition changed candidate content"),
        (
            "sampling-configuration.approved.json",
            "approved sampling transition changed candidate content",
        ),
        (
            "unit-manifest.rights-approved.json",
            "approved unit transition changed non-rights content",
        ),
    ],
)
def test_verifier_rejects_nontransition_changes(
    tmp_path: Path, filename: str, message: str
) -> None:
    packet = _candidate_copy(tmp_path)
    promote_inputs(packet, packet)
    path = packet / filename
    payload = json.loads(path.read_text())
    if filename.startswith("codebook"):
        payload["labels"][0]["definition"] += " changed"
    elif filename.startswith("sampling"):
        payload["sample_size_justification"] += " changed"
    else:
        payload["units"][0]["observed_date"] = "2026-07-02"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    readiness_path = packet / "input-readiness.approved.json"
    readiness = json.loads(readiness_path.read_text())
    role = {
        "codebook.approved.json": "codebook",
        "sampling-configuration.approved.json": "sampling_configuration",
        "unit-manifest.rights-approved.json": "unit_manifest",
    }[filename]
    readiness["approved_artifacts"][role]["sha256"] = _digest(path)
    readiness_path.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match=message):
        verify_approved_fixture_inputs(
            repository_root=packet.parents[2],
            packet_dir=packet,
            expected_approval_sha256=_digest(packet / "input-approval.approved.json"),
            expected_approved_input_readiness_sha256=_digest(readiness_path),
            expected_base_repository_commit="948d392df7fbbf49ea9b33646a0bdbd845505811",
            expected_promotion_repository_commit="0" * 40,
        )
