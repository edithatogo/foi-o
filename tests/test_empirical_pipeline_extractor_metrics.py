from __future__ import annotations

from pathlib import Path

import pytest
from test_empirical_pipeline_annotations import _locked_pair, _record

from foi_o_nz.empirical_pipeline.annotations import (
    build_adjudication_queue,
    lock_adjudication_output,
)
from foi_o_nz.empirical_pipeline.contracts import seal_record
from foi_o_nz.empirical_pipeline.extractor_metrics import (
    ExtractorMetricsContractError,
    build_adjudicated_reference,
    evaluate_extractor,
)


def _reference_pipeline(tmp_path: Path):
    fixture, packets, left, right = _locked_pair(tmp_path)
    queue = build_adjudication_queue(
        context=fixture.context,
        left_output=left,
        right_output=right,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudicator_role="role:adjudicator",
    )
    adjudication = lock_adjudication_output(
        context=fixture.context,
        queue=queue,
        records=[
            _record(
                fixture.units[1],
                "role:adjudicator",
                "no",
                spans=[{"start": 0, "end": 3}],
            )
        ],
    )
    reference = build_adjudicated_reference(
        context=fixture.context,
        left=left,
        right=right,
        adjudication=adjudication,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudication_queue=queue,
    )
    return fixture, packets, left, right, queue, adjudication, reference


def _extractor(unit: dict) -> dict:
    if unit["unit_id"] == "u1":
        return {
            "label": "yes",
            "spans": [{"start": 0, "end": 4}],
            "provenance": {"model_sha256": "a" * 64},
        }
    if unit["unit_id"] == "u2":
        return {
            "label": "yes",
            "spans": [{"start": 1, "end": 3}],
            "provenance": {},
        }
    return {"label": None, "spans": [], "provenance": {"model_sha256": "a" * 64}}


def _evaluate(
    fixture,
    packets,
    left,
    right,
    queue,
    adjudication,
    reference,
    *,
    extractor=_extractor,
    **kwargs,
):
    return evaluate_extractor(
        context=fixture.context,
        reference=reference,
        left_annotation=left,
        right_annotation=right,
        adjudication=adjudication,
        left_packet=packets["role:annotator-a"],
        right_packet=packets["role:annotator-b"],
        adjudication_queue=queue,
        extractor=extractor,
        **kwargs,
    )


def test_reference_revalidates_all_outputs_against_exact_artifacts(tmp_path: Path) -> None:
    fixture, _, _, _, _, _, reference = _reference_pipeline(tmp_path)
    assert [row["unit_id"] for row in reference["records"]] == ["u1", "u2", "u3"]
    assert reference["records"][1]["resolution"] == "adjudicated"
    assert reference["authorization_sha256"] == fixture.context.authorization_sha256


def test_extractor_metrics_use_context_vocabulary_and_emit_complete_lineage(
    tmp_path: Path,
) -> None:
    pipeline = _reference_pipeline(tmp_path)
    fixture, packets, left, right, queue, adjudication, reference = pipeline
    metrics = _evaluate(
        fixture,
        packets,
        left,
        right,
        queue,
        adjudication,
        reference,
        provenance_required_fields={"model_sha256"},
        span_iou_threshold=0.5,
    )
    assert metrics["label_metrics"]["f1"] == 0.5
    assert metrics["all_unit_exact_span"]["threshold_eligible"] is False
    assert metrics["exact_span"]["threshold_eligible"] is True
    assert metrics["span_iou"]["threshold_eligible"] is False
    assert metrics["provenance_completeness"]["threshold_eligible"] is False
    assert metrics["population_sha256"] == fixture.context.population_sha256("extractor_metrics")
    assert metrics["authorization_artifact_sha256"] == fixture.context.authorization_artifact_sha256
    assert metrics["calibration_artifact_sha256"] == fixture.context.calibration_artifact_sha256


def test_extractor_cannot_use_caller_invented_label(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)

    def invented(_unit: dict) -> dict:
        return {"label": "invented", "spans": [], "provenance": {}}

    with pytest.raises(ExtractorMetricsContractError, match="not registered"):
        _evaluate(
            fixture,
            packets,
            left,
            right,
            queue,
            adjudication,
            reference,
            extractor=invented,
        )


def test_context_unit_content_cannot_be_substituted_for_extractor(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)
    units = list(fixture.context.units)
    units[0]["text"] = "substituted"
    metrics = _evaluate(
        fixture,
        packets,
        left,
        right,
        queue,
        adjudication,
        reference,
    )
    assert metrics["unit_count"] == 3
    assert fixture.context.units[0]["text"] == "yes!"


def test_reference_rejects_substituted_approved_packet(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, _ = _reference_pipeline(tmp_path)
    with pytest.raises(ExtractorMetricsContractError):
        build_adjudicated_reference(
            context=fixture.context,
            left=left,
            right=right,
            adjudication=adjudication,
            left_packet=packets["role:annotator-b"],
            right_packet=packets["role:annotator-a"],
            adjudication_queue=queue,
        )


def test_reference_rejects_resealed_fabricated_adjudication_queue(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, _ = _reference_pipeline(tmp_path)
    queue["items"] = []
    queue = seal_record(queue, "queue_sha256")
    with pytest.raises(ExtractorMetricsContractError, match="exact annotator disagreements"):
        build_adjudicated_reference(
            context=fixture.context,
            left=left,
            right=right,
            adjudication=adjudication,
            left_packet=packets["role:annotator-a"],
            right_packet=packets["role:annotator-b"],
            adjudication_queue=queue,
        )


def test_wrong_label_cannot_inflate_threshold_eligible_span(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)
    metrics = _evaluate(
        fixture,
        packets,
        left,
        right,
        queue,
        adjudication,
        reference,
    )
    assert metrics["all_unit_exact_span"]["denominator"] == 3
    assert metrics["exact_span"]["denominator"] == 1


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("codebook_sha256", "1" * 64),
        ("calibration_sha256", "2" * 64),
        ("authorization_sha256", "3" * 64),
        ("source_bundle_sha256", "4" * 64),
    ],
)
def test_extractor_rejects_resealed_reference_lineage(
    tmp_path: Path, field: str, replacement: str
) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)
    changed = seal_record({**reference, field: replacement}, "reference_sha256")
    with pytest.raises(ExtractorMetricsContractError, match=r"reference|lineage"):
        _evaluate(
            fixture,
            packets,
            left,
            right,
            queue,
            adjudication,
            changed,
        )


def test_extractor_rejects_resealed_reference_content(tmp_path: Path) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)
    records = [dict(row) for row in reference["records"]]
    records[0] = seal_record({**records[0], "label": "no", "spans": []}, "reference_record_sha256")
    changed = seal_record({**reference, "records": records}, "reference_sha256")
    with pytest.raises(ExtractorMetricsContractError, match="reference"):
        _evaluate(
            fixture,
            packets,
            left,
            right,
            queue,
            adjudication,
            changed,
        )


@pytest.mark.parametrize(
    "prediction",
    [
        {"label": "yes", "spans": []},
        {"label": "yes", "spans": [], "provenance": {}, "extra": True},
        {"label": None, "spans": [{"start": 0, "end": 1}], "provenance": {}},
        {"label": "yes", "spans": [{"start": -1, "end": 1}], "provenance": {}},
    ],
)
def test_extractor_rejects_malformed_outputs(tmp_path: Path, prediction: dict) -> None:
    fixture, packets, left, right, queue, adjudication, reference = _reference_pipeline(tmp_path)
    with pytest.raises(ExtractorMetricsContractError):
        _evaluate(
            fixture,
            packets,
            left,
            right,
            queue,
            adjudication,
            reference,
            extractor=lambda _unit: prediction,
        )
