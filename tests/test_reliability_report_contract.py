import json
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas/json/reliability-report.schema.json"


def _report() -> dict[str, object]:
    return {
        "schema_version": "foi-o.reliability-report.v0.1.0",
        "report_id": "fixture-only",
        "status": "candidate_contract_fixture",
        "empirical_evidence": False,
        "promotion_allowed": False,
        "artifact_pins": {
            "protocol_sha256": "0" * 64,
            "sample_manifest_sha256": "a" * 64,
            "duplicate_cluster_registry_sha256": "b" * 64,
            "annotation_set_sha256": ["c" * 64, "d" * 64],
            "adjudication_set_sha256": "e" * 64,
            "codebook_revision": "fixture-codebook",
        },
        "calculation": {
            "confidence_level": 0.95,
            "confidence_interval_method": "two_sided_duplicate_cluster_bootstrap",
            "probability_weights_scope": "probability_sample_only",
            "span_coordinate_system": "utf8_character_half_open",
            "overlap_threshold": 0.5,
            "bootstrap_seed": 1729,
            "bootstrap_replicates_requested": 2000,
            "bootstrap_replicates_valid": 0,
            "bootstrap_replicates_invalid": 0,
        },
        "counts": {
            "units": 0,
            "missing_evidence": 0,
            "annotator_abstentions": [0, 0],
            "resolved_adjudications": 0,
            "unresolved_adjudications": 0,
            "label_counts": {},
        },
        "nominal_agreement": {
            "eligible_pairs": 0,
            "raw_agreement": {"numerator": 0, "denominator": 0, "estimate": None, "ci": None},
            "cohen_kappa": {"estimate": None, "ci": None},
            "kappa_undefined_reason": "no_authentic_annotations",
        },
        "span_agreement": {
            "eligible_pairs": 0,
            "exact_agreement": {"numerator": 0, "denominator": 0, "estimate": None, "ci": None},
            "overlap_f1": {"denominator": 0, "estimate": None, "ci": None},
        },
        "rates": {
            "adjudication": {"numerator": 0, "denominator": 0, "estimate": None},
            "unresolved": {"numerator": 0, "denominator": 0, "estimate": None},
        },
        "disagreements": [],
        "computed_at": None,
        "limitations": ["Schema fixture only; no reliability was calculated."],
    }


def test_candidate_reliability_fixture_is_not_empirical(tmp_path: Path) -> None:
    path = tmp_path / "reliability.json"
    path.write_text(json.dumps(_report()))
    assert not validate_json_schema(path, SCHEMA).errors


def test_computed_reliability_rejects_missing_timestamp(tmp_path: Path) -> None:
    payload = _report()
    payload.update(status="computed_human_reliability", empirical_evidence=True)
    payload["nominal_agreement"] = {
        "eligible_pairs": 10,
        "raw_agreement": {
            "numerator": 8,
            "denominator": 10,
            "estimate": 0.8,
            "ci": {"lower": 0.7, "upper": 0.9},
        },
        "cohen_kappa": {"estimate": 0.6, "ci": {"lower": 0.4, "upper": 0.8}},
        "kappa_undefined_reason": None,
    }
    path = tmp_path / "reliability.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_kappa_requires_value_or_registered_undefined_reason(tmp_path: Path) -> None:
    payload = _report()
    payload["nominal_agreement"] = {
        "eligible_pairs": 1,
        "raw_agreement": {
            "numerator": 1,
            "denominator": 1,
            "estimate": 1.0,
            "ci": {"lower": 1.0, "upper": 1.0},
        },
        "cohen_kappa": {"estimate": None, "ci": None},
        "kappa_undefined_reason": None,
    }
    path = tmp_path / "reliability.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors


def test_candidate_fixture_cannot_enable_promotion(tmp_path: Path) -> None:
    payload = _report()
    payload["promotion_allowed"] = True
    path = tmp_path / "reliability.json"
    path.write_text(json.dumps(payload))
    assert validate_json_schema(path, SCHEMA).errors
