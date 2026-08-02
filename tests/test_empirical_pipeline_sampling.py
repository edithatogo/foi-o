from __future__ import annotations

import copy

import pytest
from empirical_context_fixture import build_context_fixture

from foi_o_nz.empirical_pipeline.contracts import content_sha256, seal_record
from foi_o_nz.empirical_pipeline.frames import (
    build_candidate_frame,
    build_duplicate_cluster_registry,
    build_frame_approval,
    finalize_frame,
)
from foi_o_nz.empirical_pipeline.sampling import (
    SamplingContractError,
    build_membership,
    build_sampling_approval,
    validate_membership,
)

SHA_A = "a" * 64
SHA_B = "b" * 64


def _frame(tmp_path, *, reverse_units: bool = False, source_population_sha256: str = SHA_A) -> dict:
    units = [
        {
            "unit_id": f"unit:{index}",
            "unit_sha256": f"{index:064x}",
            "duplicate_key": "paired" if index in {0, 1} else f"unique:{index}",
            "stratum": "AU-TEST:request",
        }
        for index in range(8)
    ]
    if reverse_units:
        units.reverse()
    registry = build_duplicate_cluster_registry(units)
    candidate = build_candidate_frame(
        frame_id="frame:au-test",
        source_population_sha256=source_population_sha256,
        units=units,
        predecessor_count=8,
        excluded_ids=[],
        unresolved_ids=[],
        duplicate_registry=registry,
    )
    approval = build_frame_approval(
        candidate,
        artifact_id="frame-approval:test",
        approver_identity="human:owner",
    )
    context = build_context_fixture(
        tmp_path,
        extra_stages=(("frame", ("frame.finalize",)),),
        extra_referenced_artifacts=(
            ("frame-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    return finalize_frame(
        candidate,
        context=context,
        transition_authorization=approval,
    )


def _approved_build(tmp_path, frame: dict, **kwargs):
    approval = build_sampling_approval(
        frame,
        artifact_id="sampling-approval:test",
        approver_identity="human:owner",
        **kwargs,
    )
    context = build_context_fixture(
        tmp_path,
        extra_stages=(("sample", ("sampling.membership.prepare",)),),
        extra_referenced_artifacts=(
            ("sampling-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    membership = build_membership(
        frame,
        context=context,
        sampling_approval=approval,
        **kwargs,
    )
    return membership, context, approval


def _validate(context, approval: dict, frame: dict, membership: dict, **kwargs) -> None:
    validate_membership(
        frame,
        membership,
        context=context,
        sampling_approval=approval,
        **kwargs,
    )


def _reseal(record: dict) -> None:
    record["membership_sha256"] = content_sha256(record, "membership_sha256")


def test_unit_sample_is_order_independent_without_replacement_and_weighted(tmp_path) -> None:
    frame = _frame(tmp_path / "frame-first")
    first, context, approval = _approved_build(
        tmp_path / "sample-first",
        frame,
        design="simple_random_without_replacement",
        sampling_unit="unit",
        seed=20260721,
        sample_size=4,
    )
    second_frame = _frame(tmp_path / "frame-second", reverse_units=True)
    second, _, _ = _approved_build(
        tmp_path / "sample-second",
        second_frame,
        design="simple_random_without_replacement",
        sampling_unit="unit",
        seed=20260721,
        sample_size=4,
    )
    assert first == second
    assert len(first["membership"]) == 4
    assert len({row["unit_id"] for row in first["membership"]}) == 4
    assert {row["inclusion_probability"] for row in first["membership"]} == {0.5}
    assert {row["sampling_weight"] for row in first["membership"]} == {2.0}
    assert first["selection_algorithm"] == "sha256-ranked-without-replacement.v1"
    _validate(context, approval, frame, first)


def test_cluster_sample_selects_whole_clusters_and_uses_cluster_probability(tmp_path) -> None:
    frame = _frame(tmp_path / "frame")
    membership, context, approval = _approved_build(
        tmp_path / "sample",
        frame,
        design="simple_random_without_replacement",
        sampling_unit="duplicate_cluster",
        seed=3,
        sample_size=3,
    )
    selected_ids = {row["unit_id"] for row in membership["membership"]}
    assert ({"unit:0", "unit:1"} <= selected_ids) or not ({"unit:0", "unit:1"} & selected_ids)
    assert membership["selected_sampling_unit_count"] == 3
    assert membership["population_sampling_unit_count"] == 7
    assert {row["inclusion_probability"] for row in membership["membership"]} == {3 / 7}
    assert {row["sampling_weight"] for row in membership["membership"]} == {7 / 3}
    _validate(context, approval, frame, membership)


def test_census_selects_every_unit_with_unit_weight(tmp_path) -> None:
    frame = _frame(tmp_path / "frame")
    membership, context, approval = _approved_build(
        tmp_path / "sample",
        frame,
        design="census",
        sampling_unit="unit",
        seed=0,
        sample_size=8,
    )
    assert len(membership["membership"]) == 8
    assert {row["inclusion_probability"] for row in membership["membership"]} == {1.0}
    assert {row["sampling_weight"] for row in membership["membership"]} == {1.0}
    _validate(context, approval, frame, membership)


def test_complement_holdout_is_exact_and_has_conditional_weights(tmp_path) -> None:
    frame = _frame(tmp_path / "frame")
    prior, _, _ = _approved_build(
        tmp_path / "prior",
        frame,
        design="simple_random_without_replacement",
        sampling_unit="unit",
        seed=7,
        sample_size=5,
    )
    holdout, context, approval = _approved_build(
        tmp_path / "holdout",
        frame,
        design="complement_holdout",
        sampling_unit="unit",
        seed=7,
        sample_size=3,
        prior_membership=prior,
    )
    prior_ids = {row["unit_id"] for row in prior["membership"]}
    holdout_ids = {row["unit_id"] for row in holdout["membership"]}
    assert not prior_ids & holdout_ids
    assert prior_ids | holdout_ids == {unit["unit_id"] for unit in frame["units"]}
    assert {row["inclusion_probability"] for row in holdout["membership"]} == {1.0}
    assert {row["sampling_weight"] for row in holdout["membership"]} == {1.0}
    assert holdout["probability_basis"] == "conditional_on_pinned_prior_membership"
    assert holdout["prior_membership_sha256"] == prior["membership_sha256"]
    _validate(context, approval, frame, holdout, prior_membership=prior)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"design": "invented", "sampling_unit": "unit", "sample_size": 1}, "design"),
        (
            {
                "design": "simple_random_without_replacement",
                "sampling_unit": "invented",
                "sample_size": 1,
            },
            "sampling unit",
        ),
        (
            {
                "design": "simple_random_without_replacement",
                "sampling_unit": "unit",
                "sample_size": 0,
            },
            "sample size",
        ),
        (
            {
                "design": "simple_random_without_replacement",
                "sampling_unit": "unit",
                "sample_size": 9,
            },
            "sample size",
        ),
        ({"design": "census", "sampling_unit": "unit", "sample_size": 7}, "census"),
    ],
)
def test_sampling_rejects_invalid_designs(tmp_path, kwargs: dict, message: str) -> None:
    frame = _frame(tmp_path / "frame")
    with pytest.raises(SamplingContractError, match=message):
        _approved_build(tmp_path / "sample", frame, seed=1, **kwargs)


def test_sampling_rejects_candidate_frame(tmp_path) -> None:
    immutable = _frame(tmp_path / "frame")
    approval = build_sampling_approval(
        immutable,
        artifact_id="sampling-approval:test",
        approver_identity="human:owner",
        design="census",
        sampling_unit="unit",
        seed=0,
        sample_size=8,
    )
    context = build_context_fixture(
        tmp_path / "sample",
        extra_stages=(("sample", ("sampling.membership.prepare",)),),
        extra_referenced_artifacts=(
            ("sampling-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    candidate = copy.deepcopy(immutable)
    candidate["status"] = "candidate"
    candidate.pop("candidate_frame_sha256")
    candidate.pop("transition_authorization_sha256")
    candidate["frame_sha256"] = content_sha256(candidate, "frame_sha256")
    with pytest.raises(SamplingContractError, match="immutable"):
        build_membership(
            candidate,
            context=context,
            sampling_approval=approval,
            design="census",
            sampling_unit="unit",
            seed=0,
            sample_size=8,
        )


@pytest.mark.parametrize("mutation", ["member", "probability", "frame", "pin", "authorization"])
def test_membership_validation_recomputes_exactly_and_fails_closed(tmp_path, mutation: str) -> None:
    frame = _frame(tmp_path / "frame")
    membership, context, approval = _approved_build(
        tmp_path / "sample",
        frame,
        design="simple_random_without_replacement",
        sampling_unit="unit",
        seed=11,
        sample_size=4,
    )
    changed = copy.deepcopy(membership)
    if mutation == "member":
        changed["membership"][0]["unit_id"] = "unit:invented"
        _reseal(changed)
    elif mutation == "probability":
        changed["membership"][0]["inclusion_probability"] = 1.0
        _reseal(changed)
    elif mutation == "frame":
        changed["frame_sha256"] = SHA_A
        _reseal(changed)
    elif mutation == "pin":
        changed["membership_sha256"] = SHA_A
    else:
        changed["annotation_authorized"] = True
        _reseal(changed)
    with pytest.raises(SamplingContractError):
        _validate(context, approval, frame, changed)


def test_complement_rejects_changed_or_incomplete_prior_membership(tmp_path) -> None:
    frame = _frame(tmp_path / "frame")
    prior, _, _ = _approved_build(
        tmp_path / "prior",
        frame,
        design="simple_random_without_replacement",
        sampling_unit="unit",
        seed=7,
        sample_size=5,
    )
    changed = copy.deepcopy(prior)
    changed["membership"].pop()
    _reseal(changed)
    with pytest.raises(SamplingContractError):
        _approved_build(
            tmp_path / "holdout",
            frame,
            design="complement_holdout",
            sampling_unit="unit",
            seed=7,
            sample_size=3,
            prior_membership=changed,
        )


def test_cluster_complement_rejects_partial_prior_cluster(tmp_path) -> None:
    frame = _frame(tmp_path / "frame")
    prior, _, _ = _approved_build(
        tmp_path / "prior",
        frame,
        design="census",
        sampling_unit="duplicate_cluster",
        seed=0,
        sample_size=7,
    )
    prior["membership"] = [row for row in prior["membership"] if row["unit_id"] != "unit:0"]
    _reseal(prior)
    with pytest.raises(SamplingContractError):
        _approved_build(
            tmp_path / "holdout",
            frame,
            design="complement_holdout",
            sampling_unit="duplicate_cluster",
            seed=0,
            sample_size=0,
            prior_membership=prior,
        )


def test_sampling_rejects_bare_unverified_approval_hash() -> None:
    with pytest.raises(SamplingContractError, match="verified execution context"):
        build_membership(
            {},
            design="census",
            sampling_unit="unit",
            seed=0,
            sample_size=0,
        )


def test_sampling_rejects_registered_approval_for_unrelated_frame(tmp_path) -> None:
    approved_frame = _frame(tmp_path / "approved-frame")
    approval = build_sampling_approval(
        approved_frame,
        artifact_id="sampling-approval:test",
        approver_identity="human:owner",
        design="census",
        sampling_unit="unit",
        seed=0,
        sample_size=8,
    )
    context = build_context_fixture(
        tmp_path / "sample-context",
        extra_stages=(("sample", ("sampling.membership.prepare",)),),
        extra_referenced_artifacts=(
            ("sampling-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    unrelated = _frame(tmp_path / "unrelated-frame", source_population_sha256=SHA_B)
    with pytest.raises(SamplingContractError, match=r"frame|population|approval"):
        build_membership(
            unrelated,
            context=context,
            sampling_approval=approval,
            design="census",
            sampling_unit="unit",
            seed=0,
            sample_size=8,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("frame_sha256", SHA_B),
        ("source_population_sha256", SHA_B),
        ("duplicate_registry_sha256", SHA_B),
        ("design", "simple_random_without_replacement"),
        ("sampling_unit", "duplicate_cluster"),
        ("seed", 1),
        ("sample_size", 7),
        ("selection_algorithm", "invented.v1"),
        ("cluster_rule", "invented.v1"),
    ],
)
def test_sampling_approval_binds_every_design_input(
    tmp_path, field: str, replacement: object
) -> None:
    frame = _frame(tmp_path / "frame")
    approval = build_sampling_approval(
        frame,
        artifact_id="sampling-approval:test",
        approver_identity="human:owner",
        design="census",
        sampling_unit="unit",
        seed=0,
        sample_size=8,
    )
    approval[field] = replacement
    approval = seal_record(approval, "artifact_sha256")
    context = build_context_fixture(
        tmp_path / "sample-context",
        extra_stages=(("sample", ("sampling.membership.prepare",)),),
        extra_referenced_artifacts=(
            ("sampling-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    with pytest.raises(SamplingContractError, match=r"frame|design|approval"):
        build_membership(
            frame,
            context=context,
            sampling_approval=approval,
            design="census",
            sampling_unit="unit",
            seed=0,
            sample_size=8,
        )
