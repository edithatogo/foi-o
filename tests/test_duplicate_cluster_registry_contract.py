import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/duplicate-cluster-registry.schema.json"


def _registry() -> dict[str, object]:
    return {
        "schema_version": "foi-o.duplicate-cluster-registry.v0.1.0",
        "registry_id": "contract-fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "population_manifest_ref": "fixtures/not-an-authentic-population.json",
        "population_manifest_sha256": "a" * 64,
        "algorithm": {"name": "exact-and-near-duplicate", "version": "0.1.0", "threshold": 0.9},
        "created_at": "2026-07-17T00:00:00Z",
        "frozen_at": None,
        "clusters": [
            {
                "cluster_id": "fixture-cluster-1",
                "member_unit_sha256": ["b" * 64, "c" * 64],
                "split": "test",
            }
        ],
    }


def test_candidate_cluster_registry_is_explicitly_not_empirical(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(_registry()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_frozen_registry_requires_freeze_time_and_empirical_evidence(tmp_path: Path) -> None:
    payload = _registry()
    payload["status"] = "frozen"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors
