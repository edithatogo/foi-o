from __future__ import annotations

from pathlib import Path

import pytest
from test_empirical_pipeline_annotations import _locked_pair

from foi_o_nz.empirical_pipeline.contracts import seal_record
from foi_o_nz.empirical_pipeline.reliability import (
    ReliabilityContractError,
    compute_descriptive_reliability,
)


def _compute(tmp_path: Path):
    fixture, packets, left, right = _locked_pair(tmp_path)
    report = compute_descriptive_reliability(
        context=fixture.context,
        left=left,
        right=right,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        seed=20260721,
        replicates=50,
    )
    return fixture, packets, left, right, report


def test_reliability_is_deterministic_descriptive_and_maturity_composable(
    tmp_path: Path,
) -> None:
    fixture, packets, left, right, report = _compute(tmp_path)
    repeated = compute_descriptive_reliability(
        context=fixture.context,
        left=left,
        right=right,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        seed=20260721,
        replicates=50,
    )
    assert report == repeated
    assert report["status"] == "computed_descriptive"
    assert report["population_sha256"] == fixture.context.population_sha256("reliability")
    assert report["authorization_artifact_sha256"] == fixture.context.authorization_artifact_sha256
    assert report["calibration_artifact_sha256"] == fixture.context.calibration_artifact_sha256
    assert report["threshold_satisfaction_authorized"] is False
    assert report["all_unit_exact_span_agreement"]["threshold_eligible"] is False
    assert report["exact_span_agreement"]["threshold_eligible"] is True


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("authorization_sha256", "a" * 64),
        ("calibration_sha256", "b" * 64),
        ("packet_sha256", "c" * 64),
        ("source_bundle_sha256", "d" * 64),
    ],
)
def test_reliability_rejects_resealed_locked_lineage_substitution(
    tmp_path: Path, field: str, replacement: str
) -> None:
    fixture, packets, left, right = _locked_pair(tmp_path)
    left[field] = replacement
    left = seal_record(left, "annotation_set_sha256")
    with pytest.raises(ReliabilityContractError):
        compute_descriptive_reliability(
            context=fixture.context,
            left=left,
            right=right,
            left_packet=packets["role:annotator-a"],
            right_packet=packets["role:annotator-b"],
            seed=1,
            replicates=5,
        )


def test_reliability_requires_exact_approved_packets(tmp_path: Path) -> None:
    fixture, packets, left, right = _locked_pair(tmp_path)
    with pytest.raises(ReliabilityContractError):
        compute_descriptive_reliability(
            context=fixture.context,
            left=left,
            right=right,
            left_packet=packets["role:annotator-b"],
            right_packet=packets["role:annotator-a"],
            seed=1,
            replicates=5,
        )


def test_cluster_bootstrap_requires_exact_partition(tmp_path: Path) -> None:
    fixture, packets, left, right = _locked_pair(tmp_path)
    with pytest.raises(ReliabilityContractError, match="exact nonempty partition"):
        compute_descriptive_reliability(
            context=fixture.context,
            left=left,
            right=right,
            left_packet=packets["role:annotator-a"],
            right_packet=packets["role:annotator-b"],
            seed=1,
            replicates=5,
            cluster_by_unit={"u1": "cluster:1"},
        )
