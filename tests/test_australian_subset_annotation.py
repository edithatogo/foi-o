import pytest

from foi_o_nz.australian_subset_annotation import (
    _annotate,
    validate_adjudication_record,
    validate_annotation_packet,
    validate_annotation_record,
    validate_disagreement_queue,
    validate_metric_inputs,
)


def test_automated_role_marks_explicit_foi_as_observed() -> None:
    result = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    assert result["label"] == "observed"
    assert result["abstention"] is False


def test_automated_role_abstains_without_supported_text() -> None:
    result = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "No relevant wording",
        role="agent:au-cth-annotator-b",
    )
    assert result["label"] == "unknown"
    assert result["abstention"] is True


def test_annotation_record_validator_accepts_bounded_record() -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


@pytest.mark.parametrize(
    ("field", "value"),
    [("role", "agent:au-cth-adjudicator"), ("label", "invented"), ("unit_id", "")],
)
def test_annotation_record_validator_rejects_role_label_and_identity_drift(
    field: str, value: object
) -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "Freedom of Information request",
        role="agent:au-cth-annotator-a",
    )
    record[field] = value
    with pytest.raises(ValueError, match=r"mismatch|approved codebook|identity"):
        validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


def test_annotation_record_validator_rejects_abstention_with_span() -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "No relevant wording",
        role="agent:au-cth-annotator-a",
    )
    record["span"] = {"start": 0, "end": 1, "coordinate_system": "utf8_character_half_open"}
    with pytest.raises(ValueError, match="abstention span"):
        validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


def test_annotation_record_validator_rejects_unregistered_abstention_reason() -> None:
    record = _annotate(
        {"unit_id": "u", "unit_sha256": "a" * 64},
        "No relevant wording",
        role="agent:au-cth-annotator-a",
    )
    record["abstention_reason"] = "invented_reason"
    with pytest.raises(ValueError, match="approved codebook"):
        validate_annotation_record(record, expected_role="agent:au-cth-annotator-a")


def test_annotation_packet_validator_accepts_valid_packet() -> None:
    packet = {
        "role": "agent:au-cth-annotator-a",
        "blinded_to_peer": True,
        "blinded_to_extractor": True,
        "units": [
            {
                "unit_id": "u-001",
                "unit_sha256": "a" * 64,
                "text_filename": "u-001.txt",
                "source_spans": [{"start": 0, "end": 10}],
            }
        ],
    }
    validate_annotation_packet(packet, expected_role="agent:au-cth-annotator-a")


def test_annotation_packet_validator_rejects_leakage_or_unblinded() -> None:
    packet = {
        "role": "agent:au-cth-annotator-a",
        "blinded_to_peer": False,
        "blinded_to_extractor": True,
        "units": [
            {
                "unit_id": "u-001",
                "unit_sha256": "a" * 64,
                "text_filename": "u-001.txt",
                "label": "observed",
            }
        ],
    }
    with pytest.raises(ValueError, match="blinded to peer"):
        validate_annotation_packet(packet)

    packet["blinded_to_peer"] = True
    with pytest.raises(ValueError, match="unblinded label"):
        validate_annotation_packet(packet)


def test_adjudication_record_validator_accepts_and_rejects() -> None:
    valid = {
        "unit_id": "u-001",
        "role": "agent:au-cth-adjudicator",
        "outcome": "resolved",
        "label": "observed",
        "rationale": "Clear FOI reference in request text.",
    }
    validate_adjudication_record(valid)

    invalid = dict(valid, label="invalid_label")
    with pytest.raises(ValueError, match="approved codebook"):
        validate_adjudication_record(invalid)

    unresolved = dict(valid, outcome="unresolved", label=None)
    validate_adjudication_record(unresolved)

    unresolved_with_label = dict(valid, outcome="unresolved", label="observed")
    with pytest.raises(ValueError, match="unresolved adjudication label must be null"):
        validate_adjudication_record(unresolved_with_label)


def test_disagreement_queue_validator_accepts_and_rejects() -> None:
    queue = [
        {
            "unit_id": "u-001",
            "a_label": "observed",
            "b_label": "candidate",
            "dimension": "label",
        }
    ]
    validate_disagreement_queue(queue)

    duplicate_queue = queue + queue
    with pytest.raises(ValueError, match="duplicate unit_id"):
        validate_disagreement_queue(duplicate_queue)


def test_metric_inputs_validator_accepts_and_rejects() -> None:
    valid_report = {
        "unit_count": 10,
        "raw_label_agreement": {
            "numerator": 8,
            "denominator": 10,
            "estimate": 0.8,
        },
        "disagreement_count": 2,
        "adjudication_count": 2,
        "extractor_metrics_authorized": False,
        "gold_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    validate_metric_inputs(valid_report)

    invalid_math = dict(
        valid_report,
        raw_label_agreement={"numerator": 8, "denominator": 10, "estimate": 0.5},
    )
    with pytest.raises(ValueError, match="estimate mismatch"):
        validate_metric_inputs(invalid_math)

    unauthorized_gate = dict(valid_report, gold_promotion_authorized=True)
    with pytest.raises(ValueError, match="unauthorized"):
        validate_metric_inputs(unauthorized_gate)


def test_build_holdout_frame_candidate() -> None:
    from foi_o_nz.australian_subset_annotation import build_holdout_frame_candidate

    pop = [
        {"unit_id": f"u-{i:03d}", "unit_sha256": f"{i:02x}" * 32, "cluster_key": f"cluster-{i % 5}"}
        for i in range(20)
    ]
    calibration_clusters = {"cluster-0", "cluster-1"}
    candidate = build_holdout_frame_candidate(pop, calibration_clusters, seed=42, sample_size=8)
    assert candidate["population_count"] == 20
    assert candidate["excluded_calibration_clusters_count"] == 8
    assert candidate["eligible_count"] == 12
    assert candidate["sample_size"] == 8
    assert candidate["holdout_authorized"] is False
    assert candidate["maturity_claim_authorized"] is False


def test_compute_inter_annotator_metrics_and_maturity_candidate() -> None:
    from foi_o_nz.australian_subset_annotation import (
        build_maturity_decision_candidate,
        compute_inter_annotator_metrics,
    )

    records_a = [
        {"label": "observed", "abstention": False},
        {"label": "observed", "abstention": False},
        {"label": "candidate", "abstention": False},
        {"label": "unknown", "abstention": True},
    ]
    records_b = [
        {"label": "observed", "abstention": False},
        {"label": "observed", "abstention": False},
        {"label": "observed", "abstention": False},
        {"label": "unknown", "abstention": True},
    ]
    metrics = compute_inter_annotator_metrics(records_a, records_b)
    assert metrics["unit_count"] == 4
    assert metrics["raw_agreement"] == 0.75
    assert metrics["disagreement_count"] == 1
    assert metrics["gold_promotion_authorized"] is False

    decision = build_maturity_decision_candidate(metrics)
    assert decision["jurisdiction"] == "AU-CTH"
    assert decision["human_decision"] == "pending"
    assert decision["recommendation"] == "remediation_required"
    assert decision["gold_promotion_authorized"] is False
