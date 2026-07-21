import json
from pathlib import Path
from typing import cast

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "schemas/json"


def _validate(tmp_path: Path, name: str, payload: dict[str, object]) -> tuple[str, ...]:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(payload))
    return validate_json_schema(path, SCHEMAS / f"{name}.schema.json").errors


def _population() -> dict[str, object]:
    return {
        "schema_version": "foi-o.empirical-source-population.v0.1.0",
        "manifest_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "repository": "fixture/repository",
        "repository_revision": "a" * 40,
        "snapshot_sha256": "b" * 64,
        "rights_review_path": "fixture-only",
        "rights_review_sha256": "c" * 64,
        "coverage_start": "2026-01-01",
        "coverage_end": "2026-01-02",
        "created_at": "2026-07-17T00:00:00Z",
        "approved_by": None,
        "approved_at": None,
        "records": [
            {
                "source_artifact_sha256": "d" * 64,
                "request_linkage_key_sha256": "e" * 64,
                "observed_date": "2026-01-01",
                "source_state": "fixture-state",
                "stratum": "fixture-stratum",
                "rights_eligible": False,
                "exclusion_reason": "Contract fixture only.",
            }
        ],
    }


def _codebook() -> dict[str, object]:
    labels = [
        {
            "label": label,
            "definition": f"Synthetic definition for {label} only.",
            "positive_criteria": ["Synthetic positive criterion."],
            "negative_criteria": ["Synthetic negative criterion."],
        }
        for label in ("fixture-positive", "fixture-negative")
    ]
    return {
        "schema_version": "foi-o.annotation-codebook.v0.1.0",
        "codebook_id": "fixture-only",
        "revision": "a" * 40,
        "status": "candidate_contract_fixture",
        "protocol_sha256": "b" * 64,
        "task_type": "request_linked_candidate_assertion",
        "labels": labels,
        "span_required": True,
        "span_coordinate_system": "utf8_character_half_open",
        "overlap_threshold": 0.5,
        "abstention_reasons": [
            "missing_evidence",
            "insufficient_evidence",
            "out_of_scope",
            "other",
        ],
        "adjudication_trigger": "any_label_span_or_abstention_disagreement",
        "created_at": "2026-07-17T00:00:00Z",
        "approved_by": None,
        "approved_at": None,
    }


def _sampling() -> dict[str, object]:
    return {
        "schema_version": "foi-o.sampling-configuration.v0.1.0",
        "configuration_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "protocol_sha256": "a" * 64,
        "source_population_sha256": "b" * 64,
        "codebook_revision": "c" * 40,
        "random_seed": 1,
        "probability_sample_size": 2,
        "enrichment_sample_size": 0,
        "sample_size_justification": "Synthetic contract fixture justification only.",
        "strata": ["fixture-stratum"],
        "inclusion_probability_field": "inclusion_probability",
        "weight_field": "sampling_weight",
        "duplicate_cluster_rule": "Synthetic exact-cluster fixture rule.",
        "exclusion_rule": "Exclude anything outside the fixture.",
        "split_policy": {"grouped_by": "duplicate_cluster", "splits": ["annotation_only"]},
        "bootstrap": {
            "confidence_level": 0.95,
            "sides": "two_sided",
            "resampling_unit": "duplicate_cluster",
            "replicates": 2000,
            "interval_method": "percentile",
        },
        "created_at": "2026-07-17T00:00:00Z",
        "approved_by": None,
        "approved_at": None,
    }


def test_candidate_execution_inputs_are_schema_valid_but_unapproved(tmp_path: Path) -> None:
    assert not _validate(tmp_path, "empirical-source-population", _population())
    assert not _validate(tmp_path, "annotation-codebook", _codebook())
    assert not _validate(tmp_path, "sampling-configuration", _sampling())


def test_population_requires_eligibility_and_exclusion_reason_to_agree(tmp_path: Path) -> None:
    payload = _population()
    records = cast(list[dict[str, object]], payload["records"])
    records[0]["rights_eligible"] = True
    assert _validate(tmp_path, "empirical-source-population", payload)


def test_approved_codebook_requires_human_approval_provenance(tmp_path: Path) -> None:
    payload = _codebook()
    payload["status"] = "approved"
    assert _validate(tmp_path, "annotation-codebook", payload)


def test_approved_sampling_configuration_requires_human_provenance(tmp_path: Path) -> None:
    payload = _sampling()
    payload["status"] = "approved"
    assert _validate(tmp_path, "sampling-configuration", payload)
