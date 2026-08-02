from __future__ import annotations

import copy
from pathlib import Path

import pytest
from empirical_context_fixture import build_context_fixture

from foi_o_nz.empirical_pipeline.annotations import (
    AnnotationContractError,
    build_adjudication_queue,
    derive_disagreements,
    lock_adjudication_output,
    lock_annotation_output,
    validate_locked_adjudication_output,
    validate_locked_annotation_output,
)
from foi_o_nz.empirical_pipeline.packets import build_blinded_packets


def _record(unit: dict, role: str, label: str | None, *, spans=None) -> dict:
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
        "role_id": role,
        "label": label,
        "abstention_reason": None if label is not None else "insufficient",
        "spans": [] if spans is None else spans,
    }


def _locked_pair(tmp_path: Path):
    fixture = build_context_fixture(tmp_path)
    packets = build_blinded_packets(
        context=fixture.context,
        annotator_roles=("role:annotator-a", "role:annotator-b"),
        adjudicator_role="role:adjudicator",
    )
    units = fixture.units
    left_records = [
        _record(units[0], "role:annotator-a", "yes", spans=[{"start": 0, "end": 4}]),
        _record(units[1], "role:annotator-a", "no", spans=[{"start": 0, "end": 3}]),
        _record(units[2], "role:annotator-a", None),
    ]
    right_records = [
        _record(units[0], "role:annotator-b", "yes", spans=[{"start": 0, "end": 4}]),
        _record(units[1], "role:annotator-b", "yes", spans=[{"start": 1, "end": 3}]),
        _record(units[2], "role:annotator-b", None),
    ]
    left = lock_annotation_output(
        context=fixture.context,
        packet=packets["role:annotator-a"],
        records=left_records,
    )
    right = lock_annotation_output(
        context=fixture.context,
        packet=packets["role:annotator-b"],
        records=right_records,
    )
    return fixture, packets, left, right


def test_annotation_locking_uses_verified_codebook_and_exact_packets(tmp_path: Path) -> None:
    fixture, packets, left, _ = _locked_pair(tmp_path)
    validate_locked_annotation_output(
        left,
        context=fixture.context,
        packet=packets["role:annotator-a"],
    )
    assert left["codebook_sha256"] == fixture.context.codebook_sha256
    assert left["authorization_sha256"] == fixture.context.authorization_sha256


def test_caller_cannot_supply_invented_label_vocabulary(tmp_path: Path) -> None:
    fixture, packets, _, _ = _locked_pair(tmp_path)
    records = [
        _record(unit, "role:annotator-a", "invented_not_from_codebook") for unit in fixture.units
    ]
    with pytest.raises(AnnotationContractError, match="not registered"):
        lock_annotation_output(
            context=fixture.context,
            packet=packets["role:annotator-a"],
            records=records,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda output: output.update(authorization_sha256="a" * 64),
        lambda output: output.update(calibration_sha256="b" * 64),
        lambda output: output.update(packet_sha256="c" * 64),
        lambda output: output["annotations"][0].update(role_id="role:annotator-b"),
    ],
)
def test_resealed_locked_output_is_revalidated_against_original_artifacts(
    tmp_path: Path, mutation
) -> None:
    fixture, packets, left, _ = _locked_pair(tmp_path)
    mutation(left)
    from foi_o_nz.empirical_pipeline.contracts import seal_record

    left = seal_record(left, "annotation_set_sha256")
    with pytest.raises(AnnotationContractError):
        validate_locked_annotation_output(
            left,
            context=fixture.context,
            packet=packets["role:annotator-a"],
        )


def test_locked_output_rejects_duplicate_records_even_when_resealed(tmp_path: Path) -> None:
    fixture, packets, left, _ = _locked_pair(tmp_path)
    changed = dict(left)
    changed["annotations"] = [*left["annotations"], left["annotations"][0]]
    from foi_o_nz.empirical_pipeline.contracts import seal_record

    changed = seal_record(changed, "annotation_set_sha256")
    with pytest.raises(AnnotationContractError, match=r"unique|complete|cardinality"):
        validate_locked_annotation_output(
            changed,
            context=fixture.context,
            packet=packets["role:annotator-a"],
        )


def test_disagreements_queue_and_adjudication_are_exact_and_composable(tmp_path: Path) -> None:
    fixture, packets, left, right = _locked_pair(tmp_path)
    disagreements = derive_disagreements(left, right)
    assert [item["unit_id"] for item in disagreements] == ["u2"]
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
    validate_locked_adjudication_output(adjudication, context=fixture.context, queue=queue)
    assert adjudication["packet_sha256"] == queue["queue_sha256"]


def test_queue_rejects_output_or_packet_substitution(tmp_path: Path) -> None:
    fixture, packets, left, right = _locked_pair(tmp_path)
    substituted = copy.deepcopy(left)
    substituted["authorization_sha256"] = "a" * 64
    from foi_o_nz.empirical_pipeline.contracts import seal_record

    substituted = seal_record(substituted, "annotation_set_sha256")
    with pytest.raises(AnnotationContractError):
        build_adjudication_queue(
            context=fixture.context,
            left_output=substituted,
            right_output=right,
            left_packet=packets["role:annotator-a"],
            right_packet=packets["role:annotator-b"],
            adjudicator_role="role:adjudicator",
        )
