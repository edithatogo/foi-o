from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from empirical_context_fixture import build_context_fixture
from test_empirical_pipeline_annotations import _locked_pair
from test_empirical_pipeline_extractor_metrics import _extractor

from foi_o_nz.empirical_pipeline.contracts import parse_run_spec, seal_record
from foi_o_nz.empirical_pipeline.extractor_metrics import evaluate_extractor
from foi_o_nz.empirical_pipeline.maturity import (
    MaturityContractError,
    build_maturity_candidate,
    validate_maturity_candidate,
)
from foi_o_nz.empirical_pipeline.metric_validation import (
    MetricArtifactError,
    validate_metric_artifact,
)
from foi_o_nz.empirical_pipeline.reliability import compute_descriptive_reliability


def _metrics(tmp_path: Path):
    source_fixture, packets, left, right = _locked_pair(tmp_path / "reliability")
    reliability = compute_descriptive_reliability(
        context=source_fixture.context,
        left=left,
        right=right,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        seed=20260721,
        replicates=20,
    )
    # Reuse the same verified context for extractor evidence.
    from test_empirical_pipeline_annotations import _record

    from foi_o_nz.empirical_pipeline.annotations import (
        build_adjudication_queue,
        lock_adjudication_output,
    )
    from foi_o_nz.empirical_pipeline.extractor_metrics import build_adjudicated_reference

    queue = build_adjudication_queue(
        context=source_fixture.context,
        left_output=left,
        right_output=right,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudicator_role="role:adjudicator",
    )
    adjudication = lock_adjudication_output(
        context=source_fixture.context,
        queue=queue,
        records=[
            _record(
                source_fixture.units[1],
                "role:adjudicator",
                "no",
                spans=[{"start": 0, "end": 3}],
            )
        ],
    )
    reference = build_adjudicated_reference(
        context=source_fixture.context,
        left=left,
        right=right,
        adjudication=adjudication,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudication_queue=queue,
    )
    extractor = evaluate_extractor(
        context=source_fixture.context,
        reference=reference,
        left_annotation=left,
        right_annotation=right,
        adjudication=adjudication,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudication_queue=queue,
        extractor=_extractor,
    )
    fixture = build_context_fixture(
        tmp_path / "maturity-review",
        run_id="run:au-test-maturity",
        extra_referenced_artifacts=(
            ("reliability:test", reliability["reliability_sha256"], "restricted_local"),
            (
                "extractor-metrics:test",
                extractor["extractor_metrics_sha256"],
                "restricted_local",
            ),
        ),
    )
    return fixture, reliability, extractor


def _lifecycle(reliability: dict, extractor: dict) -> list[dict]:
    return [
        {
            "artifact_sha256": artifact[field],
            "disposition": "active",
            "superseded_by_sha256": None,
            "reason": None,
        }
        for artifact, field in (
            (reliability, "reliability_sha256"),
            (extractor, "extractor_metrics_sha256"),
        )
    ]


def test_fresh_metrics_compose_directly_into_pending_maturity_candidate(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    candidate = build_maturity_candidate(
        context=fixture.context,
        reliability=reliability,
        extractor_metrics=extractor,
        thresholds=[
            {
                "threshold_id": "label-agreement",
                "artifact": "reliability",
                "metric_path": "raw_label_agreement.estimate",
                "operator": ">=",
                "value": 0.5,
            },
            {
                "threshold_id": "extractor-f1",
                "artifact": "extractor_metrics",
                "metric_path": "label_metrics.f1",
                "operator": ">=",
                "value": 0.4,
            },
        ],
        evidence_lifecycle=_lifecycle(reliability, extractor),
    )
    validate_maturity_candidate(candidate, context=fixture.context)
    assert candidate["status"] == "pending_human_decision"
    assert candidate["decision"] is None
    assert candidate["profile_promotion_authorized"] is False
    assert candidate["population_sha256"] == fixture.context.population_sha256("maturity")


def test_maturity_rejects_threshold_over_descriptive_ineligible_metric(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    with pytest.raises(MaturityContractError, match="not eligible"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[
                {
                    "threshold_id": "inflated-span",
                    "artifact": "reliability",
                    "metric_path": "all_unit_exact_span_agreement.estimate",
                    "operator": ">=",
                    "value": 0.9,
                }
            ],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("run_id", "run:au-other"),
        ("authorization_artifact_sha256", "a" * 64),
        ("calibration_artifact_sha256", "b" * 64),
        ("population_sha256", "c" * 64),
    ],
)
def test_maturity_rejects_cross_lineage_metric_artifacts(
    tmp_path: Path, field: str, replacement: str
) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    reliability[field] = replacement
    reliability = seal_record(reliability, "reliability_sha256")
    with pytest.raises(MaturityContractError, match=r"lineage|registered"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


def test_descriptive_run_spec_cannot_execute_maturity(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    with pytest.raises(MaturityContractError, match="verified execution context"):
        build_maturity_candidate(  # type: ignore[arg-type]
            context=cast(Any, parse_run_spec(fixture.spec)),
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


def test_maturity_rejects_resealed_internally_inconsistent_metric(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    reliability["raw_label_agreement"]["estimate"] = 1.0
    reliability = seal_record(reliability, "reliability_sha256")
    with pytest.raises(MaturityContractError, match=r"metric|reliability"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[
                {
                    "threshold_id": "forged-agreement",
                    "artifact": "reliability",
                    "metric_path": "raw_label_agreement.estimate",
                    "operator": ">=",
                    "value": 0.99,
                }
            ],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


def test_maturity_rejects_unregistered_metric_path(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    reliability["invented_metric"] = {"estimate": 1.0}
    reliability = seal_record(reliability, "reliability_sha256")
    with pytest.raises(MaturityContractError, match=r"metric|schema|eligible"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[
                {
                    "threshold_id": "invented",
                    "artifact": "reliability",
                    "metric_path": "invented_metric.estimate",
                    "operator": ">=",
                    "value": 0.99,
                }
            ],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


def test_maturity_rejects_unregistered_metric_artifact_hashes(tmp_path: Path) -> None:
    _fixture, reliability, extractor = _metrics(tmp_path)
    unregistered = build_context_fixture(
        tmp_path / "unregistered-review",
        run_id="run:au-test-unregistered-review",
    )
    assert not any(
        artifact["sha256"]
        in {
            reliability["reliability_sha256"],
            extractor["extractor_metrics_sha256"],
        }
        for artifact in unregistered.context.run_spec.raw["referenced_artifacts"]
    )
    with pytest.raises(MaturityContractError, match="registered"):
        build_maturity_candidate(
            context=unregistered.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


def test_maturity_rejects_resealed_fabricated_kappa(tmp_path: Path) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    reliability["cohen_kappa"]["estimate"] = 0.999
    reliability["cohen_kappa"]["undefined_reason"] = None
    reliability = seal_record(reliability, "reliability_sha256")
    with pytest.raises(MaturityContractError, match=r"kappa|metric|registered"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[
                {
                    "threshold_id": "forged-kappa",
                    "artifact": "reliability",
                    "metric_path": "cohen_kappa.estimate",
                    "operator": ">=",
                    "value": 0.99,
                }
            ],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )


@pytest.mark.parametrize("mutation", ["kappa", "bootstrap_replicates", "bootstrap_ci"])
def test_reliability_validator_independently_recomputes_threshold_evidence(
    tmp_path: Path, mutation: str
) -> None:
    _, reliability, _ = _metrics(tmp_path)
    if mutation == "kappa":
        reliability["cohen_kappa"]["estimate"] = 0.999
    elif mutation == "bootstrap_replicates":
        reliability["cohen_kappa"]["bootstrap_replicates_valid"] -= 1
        reliability["cohen_kappa"]["bootstrap_replicates_undefined"] += 1
    else:
        reliability["raw_label_agreement"]["ci"] = {"lower": 0.0, "upper": 0.0}
    reliability = seal_record(reliability, "reliability_sha256")
    with pytest.raises(MetricArtifactError, match=r"kappa|bootstrap|confidence"):
        validate_metric_artifact(reliability, "reliability")


@pytest.mark.parametrize("metric_path", ["span_iou.estimate", "provenance_completeness.estimate"])
def test_maturity_rejects_metrics_without_independently_recomputable_rows(
    tmp_path: Path, metric_path: str
) -> None:
    fixture, reliability, extractor = _metrics(tmp_path)
    with pytest.raises(MaturityContractError, match="not eligible"):
        build_maturity_candidate(
            context=fixture.context,
            reliability=reliability,
            extractor_metrics=extractor,
            thresholds=[
                {
                    "threshold_id": "not-independent",
                    "artifact": "extractor_metrics",
                    "metric_path": metric_path,
                    "operator": ">=",
                    "value": 0.5,
                }
            ],
            evidence_lifecycle=_lifecycle(reliability, extractor),
        )
