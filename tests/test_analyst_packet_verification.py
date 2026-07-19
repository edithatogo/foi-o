import json
import shutil
from hashlib import sha256
from pathlib import Path
from subprocess import run

import pytest

from foi_o_nz.analyst_packet_verification import (
    canonical_redacted_context,
    derive_fixture_units,
    ordered_unit_commitment,
    resolve_repo_artifact,
    verify_analyst_execution_packet,
    verify_authorized_actor_separation,
    verify_fixture_manifests,
    verify_git_anchor,
)
from scripts.promote_analyst_fixture_inputs import main as promote_inputs

ROOT = Path(__file__).parents[1]
PACKET_FILES = {
    "source_population": "source-population.json",
    "codebook": "codebook.json",
    "sampling_configuration": "sampling-configuration.json",
    "unit_manifest": "unit-manifest.json",
    "duplicate_cluster_registry": "cluster-registry.json",
    "redaction_manifest": "redaction-manifest.json",
    "local_rights_review": "local-rights-review.pending.json",
}
CANDIDATE_FILES = [*PACKET_FILES.values(), "readiness.json"]
PROMOTED_FILES = {
    "source_population": "source-population.json",
    "codebook": "codebook.approved.json",
    "sampling_configuration": "sampling-configuration.approved.json",
    "unit_manifest": "unit-manifest.rights-approved.json",
    "duplicate_cluster_registry": "cluster-registry.rights-approved.json",
    "redaction_manifest": "redaction-manifest.json",
    "local_rights_review": "local-rights-review.approved.json",
}


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _committed_approved_bundle(
    tmp_path: Path, mutation: str | None = None
) -> tuple[Path, Path, str, str]:
    root = tmp_path / "repo"
    packet = root / "examples/v2/analyst-fixture-packet"
    packet.mkdir(parents=True)
    (root / "docs").mkdir()
    for relative in [
        "examples/process-mining-events.fixture.jsonl",
        "examples/event-timeline.small.json",
        "docs/42-v2-analyst-execution-protocol.md",
        "LICENSE.md",
    ]:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    for filename in CANDIDATE_FILES:
        shutil.copy2(ROOT / "examples/v2/analyst-fixture-packet" / filename, packet / filename)

    run(["git", "init", "-q"], cwd=root, check=True)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
    run(["git", "add", "."], cwd=root, check=True)
    run(["git", "commit", "-qm", "candidate"], cwd=root, check=True)
    base_commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    promote_inputs(
        packet,
        packet,
        repository_root=root,
        base_repository_commit=base_commit,
    )

    artifacts = {
        role: json.loads((packet / filename).read_text())
        for role, filename in PROMOTED_FILES.items()
    }
    if mutation == "population_source":
        artifacts["source_population"]["sources"][0]["sha256"] = "0" * 64
    elif mutation == "rights_source":
        artifacts["local_rights_review"]["sources"][0]["sha256"] = "0" * 64
    elif mutation == "license":
        artifacts["local_rights_review"]["license_placeholder"]["sha256"] = "0" * 64
    elif mutation == "codebook_protocol":
        artifacts["codebook"]["protocol_sha256"] = "0" * 64
    elif mutation == "codebook_task":
        artifacts["codebook"]["task_type"] = "request_linked_candidate_assertion"
    elif mutation == "sampling_population":
        artifacts["sampling_configuration"]["source_population_sha256"] = "0" * 64
    elif mutation == "sampling_codebook":
        artifacts["sampling_configuration"]["codebook_revision"] = "0" * 40
    elif mutation == "cluster_pin":
        artifacts["duplicate_cluster_registry"]["unit_manifest_sha256"] = "0" * 64
    elif mutation == "commitment_algorithm":
        artifacts["unit_manifest"]["ordered_unit_commitment_algorithm"] = "unregistered"
    elif mutation == "unit_rights":
        artifacts["unit_manifest"]["units"][0]["rights_eligible_for_local_use"] = False
    elif mutation == "rights_chronology":
        artifacts["local_rights_review"]["created_at"] = "2026-07-17T13:30:00Z"
    elif mutation == "codebook_chronology":
        artifacts["codebook"]["created_at"] = "2026-07-17T13:30:00Z"
    for role, filename in PROMOTED_FILES.items():
        if (
            role not in {"source_population", "redaction_manifest"}
            or mutation == "population_source"
        ):
            _write_json(packet / filename, artifacts[role])

    readiness_path = packet / "input-readiness.approved.json"
    readiness = json.loads(readiness_path.read_text())
    for role, filename in PROMOTED_FILES.items():
        section = (
            "unchanged_artifacts"
            if role in {"source_population", "redaction_manifest"}
            else "approved_artifacts"
        )
        readiness[section][role]["sha256"] = sha256((packet / filename).read_bytes()).hexdigest()
    _write_json(readiness_path, readiness)

    protocol_pin_path = "docs/42-v2-analyst-execution-protocol.md"
    if mutation == "protocol_substitution":
        protocol_pin_path = "docs/alternate.md"
        (root / protocol_pin_path).write_text("alternate protocol\n")
    pinned_protocol = root / protocol_pin_path
    pins = {
        "approved_input_readiness": {
            "path": "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
            "sha256": sha256(readiness_path.read_bytes()).hexdigest(),
            "state": "locked",
        },
        "protocol": {
            "path": protocol_pin_path,
            "sha256": sha256(pinned_protocol.read_bytes()).hexdigest(),
            "state": "locked",
        },
    }
    pins.update(
        {
            role: {
                "path": f"examples/v2/analyst-fixture-packet/{filename}",
                "sha256": sha256((packet / filename).read_bytes()).hexdigest(),
                "state": "locked",
            }
            for role, filename in PROMOTED_FILES.items()
        }
    )
    actor = lambda actor_id, role, session: {  # noqa: E731
        "actor_id": actor_id,
        "actor_class": "automated_agent",
        "role": role,
        "runtime": {
            "provider": "codex",
            "model": "recorded",
            "prompt_sha256": "a" * 64,
            "session_id": session,
        },
    }
    authorization: dict[str, object] = {
        "schema_version": "foi-o.analyst-execution-authorization.v0.2.0",
        "authorization_id": "fixture-test",
        "status": "approved_local_agent_analysis",
        "execution_allowed": True,
        "local_only": True,
        "artifacts": pins,
        "analysts": [
            actor("agent:analyst-a", "analyst", "session-a"),
            actor("agent:analyst-b", "analyst", "session-b"),
        ],
        "reconciler": actor("agent:reconciler", "reconciler", "session-r"),
        "approved_by": "human:test",
        "approved_at": "2026-07-17T14:00:00Z",
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
    authorization_path = packet / "authorization.approved.json"
    _write_json(authorization_path, authorization)
    run(["git", "add", "."], cwd=root, check=True)
    run(["git", "commit", "-qm", "promoted authorization"], cwd=root, check=True)
    commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return root, authorization_path, sha256(authorization_path.read_bytes()).hexdigest(), commit


def test_ordered_commitment_is_source_order_sensitive() -> None:
    hashes = ["a" * 64, "b" * 64]
    expected = sha256((("a" * 64) + "\n" + ("b" * 64) + "\n").encode("ascii")).hexdigest()
    assert ordered_unit_commitment(hashes) == expected
    assert ordered_unit_commitment(list(reversed(hashes))) != expected


def test_recursive_redaction_is_canonical_and_reports_removed_keys() -> None:
    value = {
        "z": {"confidence": 0.5, "kept": 1},
        "assertion_status": "candidate",
        "a": [{"confidence": 1.0, "kept": 2}],
    }
    encoded, removed = canonical_redacted_context(value)
    assert encoded == b'{"a":[{"kept":2}],"z":{"kept":1}}'
    assert removed == ("assertion_status", "confidence")


def test_repo_artifact_resolution_rejects_escape_and_symlink(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    artifact = root / "artifact.json"
    artifact.write_text("{}")
    assert resolve_repo_artifact(root, "artifact.json") == artifact.resolve()

    with pytest.raises(ValueError, match="unsafe repository-relative path"):
        resolve_repo_artifact(root, "../outside.json")

    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    link = root / "link.json"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes repository root"):
        resolve_repo_artifact(root, "link.json")


def test_actor_separation_rejects_reused_identity_or_session() -> None:
    authorization = {
        "analysts": [
            {"actor_id": "agent:analyst-a", "runtime": {"session_id": "session-a"}},
            {"actor_id": "agent:analyst-b", "runtime": {"session_id": "session-b"}},
        ],
        "reconciler": {
            "actor_id": "agent:reconciler",
            "runtime": {"session_id": "session-r"},
        },
    }
    verify_authorized_actor_separation(authorization)
    authorization["reconciler"]["runtime"]["session_id"] = "session-a"  # type: ignore[index]
    with pytest.raises(ValueError, match="actor sessions are not distinct"):
        verify_authorized_actor_separation(authorization)


def test_git_anchor_rejects_wrong_commit_and_dirty_artifact(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    run(["git", "init", "-q"], cwd=root, check=True)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
    artifact = root / "artifact.json"
    artifact.write_text("{}\n")
    run(["git", "add", "artifact.json"], cwd=root, check=True)
    run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    verify_git_anchor(root, commit, [artifact])

    with pytest.raises(ValueError, match="repository commit mismatch"):
        verify_git_anchor(root, "0" * 40, [artifact])
    artifact.write_text('{"dirty":true}\n')
    with pytest.raises(ValueError, match="differs from anchored commit"):
        verify_git_anchor(root, commit, [artifact])


def test_real_fixture_extraction_recomputes_exact_9_plus_2_census() -> None:
    units = derive_fixture_units(ROOT)
    assert len(units) == 11
    assert [unit.unit_id for unit in units[:2]] == ["pm-01", "pm-02"]
    assert [unit.unit_id for unit in units[-2:]] == ["tl-01", "tl-02"]
    assert units[0].source_span == (0, 372)
    assert (
        units[0].unit_sha256 == "bed785acf4a464c002d13e9f1d27098cf66b26ff2e5ab4e337a00916231aadc2"
    )
    assert (
        units[0].context_sha256
        == "b08edb67a9e64513dc81769a3d9144c05cd34ba474d53dbdabfb13c7ad28cbae"
    )
    assert units[-1].source_span == (597, 1124)
    assert (
        units[-1].unit_sha256 == "a7c6ace3fe8bbf3681e640d31b2641c3927f7ad6c140866ee57db05b3f9c75fd"
    )
    assert (
        units[-1].context_sha256
        == "3b1a905fa0dee289682c3895bd44c0074344487aea7d1b4a272222852bbe1860"
    )
    assert ordered_unit_commitment([unit.unit_sha256 for unit in units]) == (
        "d6e5c6b425903f09c6e3e08e0d6c4ccdee11eea91835d6ba96f64ba3306cf8ca"
    )


def test_manifest_cross_checks_require_exact_unit_redaction_cluster_bijection() -> None:
    derived = derive_fixture_units(ROOT)
    units = [
        {
            "unit_id": unit.unit_id,
            "source_path": unit.source_path,
            "source_artifact_sha256": unit.source_artifact_sha256,
            "unit_sha256": unit.unit_sha256,
            "context_sha256": unit.context_sha256,
            "source_span": {"start": unit.source_span[0], "end": unit.source_span[1]},
            "observed_date": unit.observed_date,
            "request_linkage_group": unit.request_linkage_group,
            "duplicate_cluster_id": f"exact:{unit.context_sha256}",
            "split": "annotation_only",
            "inclusion_probability": 1.0,
            "sampling_weight": 1.0,
            "rights_eligible_for_local_use": True,
        }
        for unit in derived
    ]
    unit_manifest = {
        "ordered_unit_commitment_sha256": ordered_unit_commitment(
            [unit.unit_sha256 for unit in derived]
        ),
        "ordered_unit_commitment_algorithm": "sha256_lowercase_hex_lines_final_newline_v1",
        "units": units,
    }
    redaction = {
        "entries": [
            {
                "unit_id": unit.unit_id,
                "unit_sha256": unit.unit_sha256,
                "context_sha256": unit.context_sha256,
                "removed_keys": list(unit.removed_keys),
                "forbidden_keys_absent": True,
            }
            for unit in derived
        ]
    }
    clusters = {
        "clusters": [
            {
                "cluster_id": f"exact:{unit.context_sha256}",
                "member_unit_sha256": [unit.unit_sha256],
                "split": "annotation_only",
            }
            for unit in derived
        ]
    }
    verify_fixture_manifests(derived, unit_manifest, redaction, clusters)

    clusters["clusters"][0]["member_unit_sha256"].append(derived[1].unit_sha256)
    with pytest.raises(ValueError, match="clusters must be singleton"):
        verify_fixture_manifests(derived, unit_manifest, redaction, clusters)


def test_public_verifier_requires_external_authorization_hash(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    run(["git", "init", "-q"], cwd=root, check=True)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
    authorization = root / "authorization.json"
    authorization.write_text("{}\n")
    run(["git", "add", "authorization.json"], cwd=root, check=True)
    run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    commit = run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()

    with pytest.raises(ValueError, match="authorization SHA-256 mismatch"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=authorization,
            expected_authorization_sha256="0" * 64,
            expected_repository_commit=commit,
        )


def test_public_verifier_rejects_retired_exact_committed_approved_bundle(tmp_path: Path) -> None:
    root, authorization, authorization_hash, commit = _committed_approved_bundle(tmp_path)
    with pytest.raises(ValueError, match="legacy three-role analyst authorization is retired"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=authorization,
            expected_authorization_sha256=authorization_hash,
            expected_repository_commit=commit,
        )


@pytest.mark.parametrize(
    ("mutation", "_message"),
    [
        ("population_source", "candidate readiness artifact pins mismatch"),
        ("rights_source", "approved rights transition changed candidate content"),
        ("license", "approved rights transition changed candidate content"),
        ("codebook_protocol", "approved codebook transition changed candidate content"),
        ("protocol_substitution", "protocol artifact is not the active analyst protocol"),
        ("codebook_task", "codebook.task_type"),
        ("sampling_population", "approved sampling transition changed candidate content"),
        ("sampling_codebook", "approved sampling transition changed candidate content"),
        ("cluster_pin", "approved cluster transition changed non-pin content"),
        ("commitment_algorithm", "units.ordered_unit_commitment_algorithm"),
        ("unit_rights", "approved unit transition changed non-rights content"),
        ("rights_chronology", "approved rights transition changed candidate content"),
        ("codebook_chronology", "approved codebook transition changed candidate content"),
    ],
)
def test_public_verifier_rejects_committed_relational_mutations(
    tmp_path: Path, mutation: str, _message: str
) -> None:
    root, authorization, authorization_hash, commit = _committed_approved_bundle(tmp_path, mutation)
    with pytest.raises(ValueError, match="legacy three-role analyst authorization is retired"):
        verify_analyst_execution_packet(
            repository_root=root,
            authorization_path=authorization,
            expected_authorization_sha256=authorization_hash,
            expected_repository_commit=commit,
        )
