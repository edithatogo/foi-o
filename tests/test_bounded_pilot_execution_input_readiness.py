import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
READINESS = ROOT / "examples/v2/bounded-pilot-execution-input-readiness.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-execution-input-readiness.schema.json"


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256(payload).hexdigest()


def test_readiness_is_valid_and_all_artifact_pins_match() -> None:
    result = validate_json_schema(READINESS, SCHEMA)
    assert not result.errors, result.errors
    readiness = json.loads(READINESS.read_text())
    for pin in readiness["artifacts"].values():
        assert pin["sha256"] == sha256((ROOT / pin["path"]).read_bytes()).hexdigest()


def test_readiness_is_purposive_and_non_inferential() -> None:
    readiness = json.loads(READINESS.read_text())
    sampling = readiness["sampling"]
    assert sampling["design"] == "purposive_case_pilot"
    assert sampling["random_seed"] is None
    assert sampling["inclusion_probabilities"] is None
    assert sampling["weights"] is None
    assert sampling["bootstrap"] is None
    assert sampling["population_inference_allowed"] is False
    assert sampling["archive_wide_claim_allowed"] is False


def test_readiness_has_two_units_and_singleton_clusters() -> None:
    readiness = json.loads(READINESS.read_text())
    assert [unit["request_id"] for unit in readiness["units"]] == ["11872", "35076"]
    assert all(unit["split"] == "annotation_only" for unit in readiness["units"])
    assert all(unit["inclusion_probability"] is None for unit in readiness["units"])
    assert all(unit["sampling_weight"] is None for unit in readiness["units"])
    assert all(len(cluster["member_unit_sha256"]) == 1 for cluster in readiness["clusters"])


def test_readiness_unit_and_cluster_identities_are_recomputed() -> None:
    readiness = json.loads(READINESS.read_text())
    evidence_pin = readiness["artifacts"]["evidence_manifest"]
    evidence = json.loads((ROOT / evidence_pin["path"]).read_text())
    evidence_by_request = {request["request_id"]: request for request in evidence["records"]}
    clusters = {cluster["cluster_id"]: cluster for cluster in readiness["clusters"]}

    assert readiness["request_linkage_algorithm"] == (
        "sha256_canonical_json_utf8_jurisdiction_source_system_request_id_v1"
    )
    assert readiness["unit_identity_algorithm"] == (
        "sha256_canonical_json_utf8_sort_keys_compact_evidence_record_v1"
    )
    assert readiness["cluster_algorithm"] == "request_identity_singleton_v1"

    for unit in readiness["units"]:
        request_id = unit["request_id"]
        linkage = _canonical_sha256(
            {
                "jurisdiction": "NZ",
                "request_id": request_id,
                "source_system": "fyi.org.nz",
            }
        )
        assert unit["request_linkage_sha256"] == linkage

        descriptor = {
            "schema_version": "foi-o.bounded-pilot-unit-identity.v0.1.0",
            "unit_id": unit["unit_id"],
            "request_linkage_sha256": linkage,
            "evidence_record": evidence_by_request[request_id],
            "selection_method_version": evidence["selection_method"]["version"],
        }
        assert unit["unit_sha256"] == _canonical_sha256(descriptor)

        cluster_id = f"request:{linkage}"
        assert unit["cluster_id"] == cluster_id
        assert clusters[cluster_id]["member_unit_sha256"] == [unit["unit_sha256"]]

    assert set(evidence_by_request) == {unit["request_id"] for unit in readiness["units"]}
    assert len({unit["unit_id"] for unit in readiness["units"]}) == 2
    assert set(clusters) == {unit["cluster_id"] for unit in readiness["units"]}


def test_readiness_remains_fail_closed_before_exact_approval() -> None:
    readiness = json.loads(READINESS.read_text())
    assert readiness["evidence_approved"] is True
    assert readiness["codebook_approved"] is True
    assert readiness["inputs_ready"] is False
    assert readiness["context_presentation_allowed"] is False
    assert readiness["execution_allowed"] is False
    assert readiness["empirical_evidence"] is False
    assert readiness["human_reviewed"] is False
    assert readiness["gold_eligible"] is False
