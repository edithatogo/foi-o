import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]


def _validate(
    tmp_path: Path, name: str, payload: dict[str, object], schema: str
) -> tuple[str, ...]:
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return validate_json_schema(path, ROOT / "schemas/json" / schema).errors


def _sources() -> list[dict[str, object]]:
    return [
        {"path": "examples/process-mining-events.fixture.jsonl", "sha256": "a" * 64},
        {"path": "examples/event-timeline.small.json", "sha256": "b" * 64},
    ]


def test_pending_rights_review_cannot_enable_execution(tmp_path: Path) -> None:
    payload = {
        "schema_version": "foi-o.analyst-local-rights-review.v0.1.0",
        "review_id": "local-fixtures",
        "status": "pending_exact_human_approval",
        "purpose": "bounded_local_agent_analysis",
        "sources": _sources(),
        "license_placeholder": {
            "path": "LICENSE.md",
            "sha256": "c" * 64,
            "grants_redistribution": False,
        },
        "local_analysis_allowed": False,
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "redistribution_granted": False,
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
        "created_at": "2026-07-17T00:00:00Z",
        "approved_by": None,
        "approved_at": None,
    }
    assert not _validate(
        tmp_path, "rights.json", payload, "analyst-local-rights-review.schema.json"
    )
    payload["local_analysis_allowed"] = True
    assert _validate(tmp_path, "rights.json", payload, "analyst-local-rights-review.schema.json")


def test_fixture_population_preserves_missing_source_state(tmp_path: Path) -> None:
    sources = _sources()
    sources[0]["expected_units"] = 9
    sources[1]["expected_units"] = 2
    payload = {
        "schema_version": "foi-o.analyst-fixture-source-population.v0.1.0",
        "population_id": "fixture-census-11",
        "status": "locked_synthetic_fixture_population",
        "task": "fixture_engineering_classification",
        "sources": sources,
        "expected_unit_count": 11,
        "coverage_start": "2026-06-01",
        "coverage_end": "2026-07-09",
        "source_state_policy": "preserve_present_null_or_absent_never_synthesize",
        "local_only": True,
        "empirical_evidence": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "release_qualifying": False,
        "publication_eligible": False,
        "created_at": "2026-07-17T00:00:00Z",
        "locked_at": "2026-07-17T00:01:00Z",
    }
    assert not _validate(
        tmp_path, "population.json", payload, "analyst-fixture-source-population.schema.json"
    )
    payload["source_state_policy"] = "derive_from_lifecycle_state"
    assert _validate(
        tmp_path, "population.json", payload, "analyst-fixture-source-population.schema.json"
    )


def test_fixture_codebook_uses_dedicated_engineering_task(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "examples/v2/analyst-fixture-packet/codebook.json").read_text())
    assert not _validate(tmp_path, "codebook.json", payload, "analyst-fixture-codebook.schema.json")
    payload["task_type"] = "request_linked_candidate_assertion"
    assert _validate(tmp_path, "codebook.json", payload, "analyst-fixture-codebook.schema.json")


def test_readiness_is_inputs_only_and_cannot_enable_execution(tmp_path: Path) -> None:
    payload = {
        "status": "pending_exact_human_rights_and_execution_input_approval",
        "protocol": {
            "path": "docs/42-v2-analyst-execution-protocol.md",
            "sha256": "a" * 64,
        },
        "artifacts": [
            {"path": f"examples/v2/analyst-fixture-packet/{name}", "sha256": f"{index:064x}"}
            for index, name in enumerate(
                [
                    "source-population.json",
                    "codebook.json",
                    "sampling-configuration.json",
                    "unit-manifest.json",
                    "cluster-registry.json",
                    "redaction-manifest.json",
                    "local-rights-review.pending.json",
                ],
                1,
            )
        ],
        "execution_allowed": False,
        "local_only": True,
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
        tmp_path, "readiness.json", payload, "analyst-fixture-readiness.schema.json"
    )
    payload["execution_allowed"] = True
    assert _validate(tmp_path, "readiness.json", payload, "analyst-fixture-readiness.schema.json")
    payload["execution_allowed"] = False
    payload["artifacts"][0]["path"] = "examples/v2/analyst-fixture-packet/unexpected.json"
    assert _validate(tmp_path, "readiness.json", payload, "analyst-fixture-readiness.schema.json")
