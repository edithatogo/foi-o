import json
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import TypedDict

import pytest

from foi_o_nz.empirical_verification import verify_authentic_empirical_bundle


class BundleArgs(TypedDict):
    authorization_path: Path
    protocol_path: Path
    source_population_path: Path
    codebook_path: Path
    sampling_configuration_path: Path
    sample_manifest_path: Path
    unit_manifest_path: Path
    duplicate_cluster_registry_path: Path
    annotation_set_paths: tuple[Path, Path]
    adjudication_set_path: Path
    reliability_report_path: Path
    expected_reliability_report_sha256: str


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def _write_jsonl(path: Path, values: Sequence[Mapping[str, object]]) -> None:
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values))


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _record_digest(record: dict[str, object]) -> str:
    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _annotation(unit: str, annotator: str, label: str, end: int) -> dict[str, object]:
    return {
        "schema_version": "foi-o.locked-annotation-record.v0.1.0",
        "record_id": f"{annotator}-{unit[:4]}",
        "status": "locked_human_annotation",
        "empirical_evidence": True,
        "unit_sha256": unit,
        "annotator_id": annotator,
        "codebook_revision": "1" * 40,
        "label": label,
        "span": {"start": 0, "end": end, "coordinate_system": "utf8_character_half_open"},
        "uncertainty": 0.0,
        "abstention": False,
        "abstention_reason": None,
        "notes": "Synthetic verifier test record; not empirical evidence.",
        "blinded_to_candidate": True,
        "created_at": "2026-07-17T02:00:00Z",
        "locked_at": "2026-07-17T03:00:00Z",
    }


def _bundle(
    tmp_path: Path,
    *,
    same_annotator: bool = False,
    overlapping_adjudicator: bool = False,
    bad_ref: bool = False,
) -> BundleArgs:
    paths = {
        name: tmp_path / name
        for name in (
            "authorization.json",
            "protocol.md",
            "source-population.json",
            "codebook.json",
            "sampling-configuration.json",
            "sample.json",
            "units.json",
            "clusters.json",
            "annotations-a.jsonl",
            "annotations-b.jsonl",
            "adjudications.jsonl",
            "reliability.json",
        )
    }
    paths["protocol.md"].write_text("Synthetic protocol fixture; no approval.\n")
    _write_json(paths["source-population.json"], {"fixture": "synthetic source population"})
    _write_json(paths["codebook.json"], {"revision": "1" * 40, "fixture": True})
    _write_json(paths["sampling-configuration.json"], {"seed": 1, "fixture": True})
    first_unit, second_unit = "a" * 64, "b" * 64
    population_sha = _digest(paths["source-population.json"])
    units = {
        "schema_version": "foi-o.empirical-unit-manifest.v0.1.0",
        "manifest_id": "synthetic-test",
        "status": "frozen",
        "empirical_evidence": True,
        "source_population_manifest_sha256": population_sha,
        "sampling_protocol_sha256": _digest(paths["protocol.md"]),
        "sampling_configuration_sha256": _digest(paths["sampling-configuration.json"]),
        "created_at": "2026-07-17T00:00:00Z",
        "frozen_at": "2026-07-17T01:00:00Z",
        "units": [
            {
                "unit_sha256": unit,
                "source_artifact_sha256": "e" * 64,
                "source_span": {
                    "start": 0,
                    "end": 4,
                    "coordinate_system": "utf8_character_half_open",
                },
                "request_linkage_key_sha256": linkage * 64,
                "duplicate_cluster_id": cluster,
                "split": "annotation_only",
                "stratum": "synthetic",
                "sample_component": "probability",
                "inclusion_probability": 1.0,
                "sampling_weight": 1.0,
                "accessibility": "accessible",
                "rights_eligible": True,
            }
            for unit, linkage, cluster in (
                (first_unit, "f", "cluster-1"),
                (second_unit, "0", "cluster-2"),
            )
        ],
    }
    _write_json(paths["units.json"], units)
    clusters = {
        "schema_version": "foi-o.duplicate-cluster-registry.v0.1.0",
        "registry_id": "synthetic-test",
        "status": "frozen",
        "empirical_evidence": True,
        "population_manifest_ref": "synthetic",
        "population_manifest_sha256": population_sha,
        "algorithm": {"name": "synthetic-exact", "version": "1", "threshold": 1.0},
        "created_at": "2026-07-17T00:00:00Z",
        "frozen_at": "2026-07-17T01:00:00Z",
        "clusters": [
            {
                "cluster_id": "cluster-1",
                "member_unit_sha256": [first_unit],
                "split": "annotation_only",
            },
            {
                "cluster_id": "cluster-2",
                "member_unit_sha256": [second_unit],
                "split": "annotation_only",
            },
        ],
    }
    _write_json(paths["clusters.json"], clusters)
    sample = {
        "sample_id": "synthetic-test",
        "population": {
            "definition": "Synthetic verifier-only population, not empirical evidence.",
            "coverage_start": "2026-01-01",
            "coverage_end": "2026-01-02",
            "unit": "request_linked_candidate_assertion",
        },
        "snapshot_ref": {"snapshot_id": "synthetic", "manifest_sha256": population_sha},
        "sampling_design": {
            "design_type": "census",
            "population_estimation_allowed": False,
            "weights_available": False,
        },
        "random_seed": 1,
        "unit_manifest_ref": "units.json",
        "unit_manifest_sha256": _digest(paths["units.json"]),
        "duplicate_cluster_registry_ref": "clusters.json",
        "duplicate_cluster_registry_sha256": _digest(paths["clusters.json"]),
        "split_policy": {"grouped_by": ["duplicate_cluster"], "splits": ["annotation_only"]},
        "created_at": "2026-07-17T01:00:00Z",
    }
    _write_json(paths["sample.json"], sample)
    annotator_a = "human:synthetic-a"
    annotator_b = annotator_a if same_annotator else "human:synthetic-b"
    annotations_a = [
        _annotation(first_unit, annotator_a, "yes", 2),
        _annotation(second_unit, annotator_a, "yes", 2),
    ]
    annotations_b = [
        _annotation(first_unit, annotator_b, "yes", 2),
        _annotation(second_unit, annotator_b, "no", 3),
    ]
    _write_jsonl(paths["annotations-a.jsonl"], annotations_a)
    _write_jsonl(paths["annotations-b.jsonl"], annotations_b)
    adjudicator = annotator_a if overlapping_adjudicator else "human:synthetic-adjudicator"
    authorization = {
        "schema_version": "foi-o.empirical-execution-authorization.v0.1.0",
        "authorization_id": "synthetic-verifier-test",
        "status": "approved_human_authorization",
        "execution_allowed": True,
        "protocol": {
            "path": "protocol.md",
            "sha256": _digest(paths["protocol.md"]),
            "approved": True,
        },
        "source_population": {
            "path": "source-population.json",
            "sha256": _digest(paths["source-population.json"]),
            "approved": True,
        },
        "codebook": {
            "path": "codebook.json",
            "sha256": _digest(paths["codebook.json"]),
            "approved": True,
        },
        "codebook_revision": "1" * 40,
        "sampling_configuration": {
            "path": "sampling-configuration.json",
            "sha256": _digest(paths["sampling-configuration.json"]),
            "approved": True,
        },
        "annotator_ids": ["human:synthetic-a", "human:synthetic-b"],
        "adjudicator_id": "human:synthetic-adjudicator",
        "approved_by": "human:synthetic-approver",
        "approved_at": "2026-07-16T23:00:00Z",
        "agents_may_fill_human_roles": False,
        "limitations": ["Synthetic verifier test authorization; no real approval."],
    }
    _write_json(paths["authorization.json"], authorization)
    refs = [
        {"annotator_id": record["annotator_id"], "sha256": _record_digest(record)}
        for record in (annotations_a[1], annotations_b[1])
    ]
    if bad_ref:
        refs[0]["sha256"] = "9" * 64
    adjudications = [
        {
            "schema_version": "foi-o.adjudication-record.v0.1.0",
            "record_id": "synthetic-adjudication",
            "status": "locked_human_adjudication",
            "empirical_evidence": True,
            "unit_sha256": second_unit,
            "annotation_refs": refs,
            "adjudicator_id": adjudicator,
            "outcome": "resolved",
            "adjudicated_label": "yes",
            "adjudicated_span": {
                "start": 0,
                "end": 2,
                "coordinate_system": "utf8_character_half_open",
            },
            "rationale": "Synthetic verifier test decision; not empirical evidence.",
            "created_at": "2026-07-17T04:00:00Z",
            "locked_at": "2026-07-17T05:00:00Z",
        }
    ]
    _write_jsonl(paths["adjudications.jsonl"], adjudications)
    report = {
        "schema_version": "foi-o.reliability-report.v0.1.0",
        "report_id": "synthetic-test",
        "status": "computed_human_reliability",
        "empirical_evidence": True,
        "promotion_allowed": False,
        "artifact_pins": {
            "authorization_sha256": _digest(paths["authorization.json"]),
            "protocol_sha256": _digest(paths["protocol.md"]),
            "sample_manifest_sha256": _digest(paths["sample.json"]),
            "duplicate_cluster_registry_sha256": _digest(paths["clusters.json"]),
            "annotation_set_sha256": [
                _digest(paths["annotations-a.jsonl"]),
                _digest(paths["annotations-b.jsonl"]),
            ],
            "adjudication_set_sha256": _digest(paths["adjudications.jsonl"]),
            "codebook_revision": "1" * 40,
        },
        "calculation": {
            "confidence_level": 0.95,
            "confidence_interval_method": "two_sided_duplicate_cluster_bootstrap",
            "probability_weights_scope": "probability_sample_only",
            "span_coordinate_system": "utf8_character_half_open",
            "overlap_threshold": 0.5,
            "bootstrap_seed": 1,
            "bootstrap_replicates_requested": 2000,
            "bootstrap_replicates_valid": 2000,
            "bootstrap_replicates_invalid": 0,
        },
        "counts": {
            "units": 2,
            "missing_evidence": 0,
            "annotator_abstentions": [0, 0],
            "resolved_adjudications": 1,
            "unresolved_adjudications": 0,
            "label_counts": {"yes": 3, "no": 1},
        },
        "nominal_agreement": {
            "eligible_pairs": 2,
            "raw_agreement": {
                "numerator": 1,
                "denominator": 2,
                "estimate": 0.5,
                "ci": {"lower": 0.0, "upper": 1.0},
            },
            "cohen_kappa": {"estimate": 0.0, "ci": {"lower": -1.0, "upper": 1.0}},
            "kappa_undefined_reason": None,
        },
        "span_agreement": {
            "eligible_pairs": 2,
            "exact_agreement": {
                "numerator": 1,
                "denominator": 2,
                "estimate": 0.5,
                "ci": {"lower": 0.0, "upper": 1.0},
            },
            "overlap_f1": {"denominator": 2, "estimate": 0.9, "ci": {"lower": 0.0, "upper": 1.0}},
        },
        "rates": {
            "adjudication": {"numerator": 1, "denominator": 1, "estimate": 1.0},
            "unresolved": {"numerator": 0, "denominator": 1, "estimate": 0.0},
        },
        "disagreements": [{"dimension": "label", "value": "yes/no", "count": 1}],
        "computed_at": "2026-07-17T06:00:00Z",
        "limitations": ["Synthetic verifier test values; not empirical evidence."],
    }
    _write_json(paths["reliability.json"], report)
    return {
        "authorization_path": paths["authorization.json"],
        "protocol_path": paths["protocol.md"],
        "source_population_path": paths["source-population.json"],
        "codebook_path": paths["codebook.json"],
        "sampling_configuration_path": paths["sampling-configuration.json"],
        "sample_manifest_path": paths["sample.json"],
        "unit_manifest_path": paths["units.json"],
        "duplicate_cluster_registry_path": paths["clusters.json"],
        "annotation_set_paths": (paths["annotations-a.jsonl"], paths["annotations-b.jsonl"]),
        "adjudication_set_path": paths["adjudications.jsonl"],
        "reliability_report_path": paths["reliability.json"],
        "expected_reliability_report_sha256": _digest(paths["reliability.json"]),
    }


def test_authentic_bundle_relationships_validate_without_promotion(tmp_path: Path) -> None:
    result = verify_authentic_empirical_bundle(**_bundle(tmp_path))
    assert result.unit_count == 2
    assert result.adjudication_count == 1
    assert result.promotion_allowed is False


@pytest.mark.parametrize(
    ("option", "message"),
    [
        ("same_annotator", "annotator identities are not distinct"),
        ("overlapping_adjudicator", "reconciler is not a distinct supported actor"),
        ("bad_ref", "adjudication annotation reference mismatch"),
    ],
)
def test_bundle_rejects_role_and_reference_mismatches(
    tmp_path: Path, option: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        verify_authentic_empirical_bundle(
            **_bundle(
                tmp_path,
                same_annotator=option == "same_annotator",
                overlapping_adjudicator=option == "overlapping_adjudicator",
                bad_ref=option == "bad_ref",
            )
        )


def test_bundle_rejects_report_accounting_drift(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    path = bundle["reliability_report_path"]
    report = json.loads(path.read_text())
    report["counts"]["units"] = 3
    _write_json(path, report)
    bundle["expected_reliability_report_sha256"] = _digest(path)
    with pytest.raises(ValueError, match="unit count mismatch"):
        verify_authentic_empirical_bundle(**bundle)


def test_bundle_rejects_statistic_drift(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    path = bundle["reliability_report_path"]
    report = json.loads(path.read_text())
    report["nominal_agreement"]["cohen_kappa"]["estimate"] = 0.2
    _write_json(path, report)
    bundle["expected_reliability_report_sha256"] = _digest(path)
    with pytest.raises(ValueError, match="Cohen kappa estimate mismatch"):
        verify_authentic_empirical_bundle(**bundle)


def test_bundle_rejects_artifact_byte_drift(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["protocol_path"].write_text("drift\n")
    with pytest.raises(ValueError, match="protocol SHA-256 mismatch"):
        verify_authentic_empirical_bundle(**bundle)
