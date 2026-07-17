import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/empirical-unit-manifest.schema.json"


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "foi-o.empirical-unit-manifest.v0.1.0",
        "manifest_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "source_population_manifest_sha256": "a" * 64,
        "sampling_protocol_sha256": "b" * 64,
        "sampling_configuration_sha256": "c" * 64,
        "created_at": "2026-07-17T00:00:00Z",
        "frozen_at": None,
        "units": [
            {
                "unit_sha256": "d" * 64,
                "source_artifact_sha256": "e" * 64,
                "source_span": {
                    "start": 0,
                    "end": 1,
                    "coordinate_system": "utf8_character_half_open",
                },
                "request_linkage_key_sha256": "f" * 64,
                "duplicate_cluster_id": "fixture-cluster",
                "split": "annotation_only",
                "stratum": "fixture-stratum",
                "sample_component": "probability",
                "inclusion_probability": 0.5,
                "sampling_weight": 2.0,
                "accessibility": "accessible",
                "rights_eligible": True,
            }
        ],
    }


def test_candidate_unit_manifest_is_not_empirical(tmp_path: Path) -> None:
    path = tmp_path / "units.json"
    path.write_text(json.dumps(_manifest()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_frozen_manifest_requires_empirical_rights_eligible_units(tmp_path: Path) -> None:
    payload = _manifest()
    payload.update(status="frozen", empirical_evidence=True, frozen_at="2026-07-17T01:00:00Z")
    payload["units"][0]["rights_eligible"] = False
    path = tmp_path / "units.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_probability_unit_requires_probability_and_weight(tmp_path: Path) -> None:
    payload = _manifest()
    payload["units"][0]["sampling_weight"] = None
    path = tmp_path / "units.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors
