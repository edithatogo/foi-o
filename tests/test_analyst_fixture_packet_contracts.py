import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema
from scripts.build_analyst_fixture_packet import main as build_fixture_packet

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "schemas/json"


def _validate(tmp_path: Path, name: str, payload: dict[str, object], schema: str) -> list[str]:
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return validate_json_schema(path, SCHEMAS / schema).errors


def _pin(path: str) -> dict[str, object]:
    return {"path": path, "sha256": "a" * 64, "state": "locked"}


def test_generated_packet_is_byte_stable_and_every_artifact_validates(tmp_path: Path) -> None:
    generated = tmp_path / "packet"
    build_fixture_packet(generated)
    schema_by_file = {
        "source-population.json": "analyst-fixture-source-population.schema.json",
        "codebook.json": "analyst-fixture-codebook.schema.json",
        "sampling-configuration.json": "sampling-configuration.schema.json",
        "unit-manifest.json": "analyst-fixture-unit-manifest.schema.json",
        "cluster-registry.json": "analyst-fixture-cluster-registry.schema.json",
        "redaction-manifest.json": "analyst-redaction-manifest.schema.json",
        "local-rights-review.pending.json": "analyst-local-rights-review.schema.json",
        "readiness.json": "analyst-fixture-readiness.schema.json",
    }
    committed = ROOT / "examples/v2/analyst-fixture-packet"
    assert {path.name for path in generated.iterdir()} == set(schema_by_file)
    for filename, schema in schema_by_file.items():
        generated_path = generated / filename
        assert generated_path.read_bytes() == (committed / filename).read_bytes()
        assert not validate_json_schema(generated_path, SCHEMAS / schema).errors


def test_non_empirical_fixture_unit_manifest_is_lockable(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-fixture-unit-manifest.v0.1.0",
        "manifest_id": "fixture-census-11",
        "status": "locked_local_fixture_census",
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "ordered_unit_commitment_sha256": "b" * 64,
        "ordered_unit_commitment_algorithm": "sha256_lowercase_hex_lines_final_newline_v1",
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": "2026-07-17T00:01:00Z",
        "units": [
            {
                "unit_id": "pm-01",
                "source_path": "examples/process-mining-events.fixture.jsonl",
                "source_artifact_sha256": "c" * 64,
                "unit_sha256": "d" * 64,
                "context_sha256": "e" * 64,
                "source_span": {
                    "start": 0,
                    "end": 372,
                    "coordinate_system": "utf8_character_half_open",
                },
                "observed_date": "2026-07-01",
                "request_linkage_group": "fixture:pm-001",
                "duplicate_cluster_id": "exact:e",
                "split": "annotation_only",
                "inclusion_probability": 1.0,
                "sampling_weight": 1.0,
                "rights_eligible_for_local_use": True,
            }
        ],
    }
    template = payload["units"][0]  # type: ignore[index]
    payload["units"] = [
        dict(
            template,
            unit_id=f"pm-{index:02d}",
            unit_sha256=f"{index:064x}",
            context_sha256=f"{index + 20:064x}",
            duplicate_cluster_id=f"exact:{index:02d}",
        )
        for index in range(1, 12)
    ]
    assert not _validate(
        tmp_path, "units.json", payload, "analyst-fixture-unit-manifest.schema.json"
    )
    payload["empirical_evidence"] = True
    assert _validate(tmp_path, "units.json", payload, "analyst-fixture-unit-manifest.schema.json")


def test_non_empirical_fixture_clusters_are_locked_and_singleton(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-fixture-cluster-registry.v0.1.0",
        "registry_id": "fixture-exact-content",
        "status": "locked_local_fixture_clusters",
        "local_only": True,
        "empirical_evidence": False,
        "release_qualifying": False,
        "unit_manifest_sha256": "a" * 64,
        "algorithm": {"name": "exact_redacted_context_sha256", "version": "1", "threshold": 1.0},
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": "2026-07-17T00:01:00Z",
        "clusters": [
            {"cluster_id": "exact:e", "member_unit_sha256": ["d" * 64], "split": "annotation_only"}
        ],
    }
    payload["human_reviewed"] = False
    payload["gold_eligible"] = False
    payload["publication_eligible"] = False
    payload["clusters"] = [
        {
            "cluster_id": f"exact:{index:02d}",
            "member_unit_sha256": [f"{index:064x}"],
            "split": "annotation_only",
        }
        for index in range(1, 12)
    ]
    assert not _validate(
        tmp_path, "clusters.json", payload, "analyst-fixture-cluster-registry.schema.json"
    )
    payload["clusters"][0]["member_unit_sha256"].append("f" * 64)  # type: ignore[index]
    assert _validate(
        tmp_path, "clusters.json", payload, "analyst-fixture-cluster-registry.schema.json"
    )


def test_redaction_manifest_locks_forbidden_keys_and_canonicalization(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-redaction-manifest.v0.1.0",
        "manifest_id": "fixture-redaction-v1",
        "status": "locked",
        "forbidden_keys": ["assertion_status", "confidence"],
        "canonicalization": {
            "parse": "json_object",
            "ensure_ascii": False,
            "sort_keys": True,
            "separators": [",", ":"],
            "encoding": "utf-8",
        },
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": "2026-07-17T00:01:00Z",
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "entries": [
            {
                "unit_id": f"unit-{index:02d}",
                "unit_sha256": f"{index:064x}",
                "context_sha256": f"{index + 20:064x}",
                "removed_keys": ["assertion_status"],
                "forbidden_keys_absent": True,
            }
            for index in range(1, 12)
        ],
    }
    assert not _validate(
        tmp_path, "redaction.json", payload, "analyst-redaction-manifest.schema.json"
    )
    payload["forbidden_keys"] = ["assertion_status"]
    assert _validate(tmp_path, "redaction.json", payload, "analyst-redaction-manifest.schema.json")


def test_authorization_requires_every_execution_artifact_pin(tmp_path: Path) -> None:
    actor = lambda actor_id, role: {  # noqa: E731
        "actor_id": actor_id,
        "actor_class": "automated_agent",
        "role": role,
        "runtime": {
            "provider": "codex",
            "model": "recorded",
            "prompt_sha256": "b" * 64,
            "session_id": actor_id,
        },
    }
    payload = {
        "schema_version": "foi-o.analyst-execution-authorization.v0.2.0",
        "authorization_id": "fixture-local-run",
        "status": "approved_local_agent_analysis",
        "execution_allowed": True,
        "local_only": True,
        "artifacts": {
            name: _pin(f"examples/v2/{name}.json")
            for name in [
                "approved_input_readiness",
                "protocol",
                "source_population",
                "codebook",
                "sampling_configuration",
                "unit_manifest",
                "duplicate_cluster_registry",
                "redaction_manifest",
                "local_rights_review",
            ]
        },
        "analysts": [actor("agent:analyst-a", "analyst"), actor("agent:analyst-b", "analyst")],
        "reconciler": actor("agent:reconciler", "reconciler"),
        "approved_by": "human:edithatogo",
        "approved_at": "2026-07-17T00:00:00Z",
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
    assert not _validate(
        tmp_path, "auth.json", payload, "analyst-execution-authorization.v0.2.schema.json"
    )
    del payload["artifacts"]["redaction_manifest"]  # type: ignore[index]
    assert _validate(
        tmp_path, "auth.json", payload, "analyst-execution-authorization.v0.2.schema.json"
    )
