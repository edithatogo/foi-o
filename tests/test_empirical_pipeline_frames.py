from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
from empirical_context_fixture import build_context_fixture

from foi_o_nz.empirical_pipeline.contracts import content_sha256, seal_record
from foi_o_nz.empirical_pipeline.frames import (
    FrameContractError,
    build_candidate_frame,
    build_duplicate_cluster_registry,
    build_frame_approval,
    finalize_frame,
    validate_duplicate_cluster_registry,
    validate_frame,
    validate_units,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
FRAME_APPROVAL_SHA = "d" * 64


def _frame_context(tmp_path):
    approval = _frame_approval(_candidate())
    return build_context_fixture(
        tmp_path,
        extra_stages=(("frame", ("frame.finalize",)),),
        extra_referenced_artifacts=(
            ("frame-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context


def _units() -> list[dict[str, object]]:
    return [
        {
            "unit_id": "unit:3",
            "unit_sha256": "3" * 64,
            "duplicate_key": "same",
            "stratum": "AU-TEST:request",
        },
        {
            "unit_id": "unit:1",
            "unit_sha256": "1" * 64,
            "duplicate_key": "unique",
            "stratum": "AU-TEST:request",
        },
        {
            "unit_id": "unit:2",
            "unit_sha256": "2" * 64,
            "duplicate_key": "same",
            "stratum": "AU-TEST:request",
        },
    ]


def _candidate() -> dict:
    units = _units()
    registry = build_duplicate_cluster_registry(units)
    return build_candidate_frame(
        frame_id="frame:au-test",
        source_population_sha256=SHA_A,
        units=units,
        predecessor_count=5,
        excluded_ids=["excluded:1"],
        unresolved_ids=["unresolved:1"],
        duplicate_registry=registry,
    )


def _frame_approval(candidate: dict) -> dict:
    return build_frame_approval(
        candidate,
        artifact_id="frame-approval:test",
        approver_identity="human:owner",
    )


def _reseal(record: dict, field: str) -> None:
    record[field] = content_sha256(record, field)


def test_units_are_canonicalized_by_identity() -> None:
    first = validate_units(_units())
    second = validate_units(list(reversed(_units())))
    assert first == second
    assert [unit["unit_id"] for unit in first] == ["unit:1", "unit:2", "unit:3"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda units: units.append(copy.deepcopy(units[0])), "duplicate unit identity"),
        (lambda units: units.__setitem__(1, {**units[1], "unit_sha256": "3" * 64}), "duplicate"),
        (lambda units: units[0].update(unit_sha256="not-a-digest"), "SHA-256"),
        (lambda units: units[0].update(extra="invented"), "canonical fields"),
        (lambda units: units[0].pop("duplicate_key"), "canonical fields"),
        (lambda units: units[0].update(stratum=""), "stratum"),
    ],
)
def test_unit_validation_fails_closed(mutation, message: str) -> None:
    units = _units()
    mutation(units)
    with pytest.raises(FrameContractError, match=message):
        validate_units(units)


def test_duplicate_clusters_are_deterministic_and_cover_every_unit_once() -> None:
    first = build_duplicate_cluster_registry(_units())
    second = build_duplicate_cluster_registry(list(reversed(_units())))
    assert first == second
    assert first["unit_count"] == 3
    assert first["cluster_count"] == 2
    validate_duplicate_cluster_registry(_units(), first)


@pytest.mark.parametrize("mutation", ["membership", "cluster_id", "self_pin"])
def test_duplicate_registry_rejects_tampering(mutation: str) -> None:
    registry = build_duplicate_cluster_registry(_units())
    changed = copy.deepcopy(registry)
    if mutation == "membership":
        changed["clusters"][0]["unit_ids"].append("unit:invented")
        _reseal(changed, "registry_sha256")
    elif mutation == "cluster_id":
        changed["clusters"][0]["cluster_id"] = "cluster:sha256:" + "f" * 64
        _reseal(changed, "registry_sha256")
    else:
        changed["registry_sha256"] = SHA_B
    with pytest.raises(FrameContractError):
        validate_duplicate_cluster_registry(_units(), changed)


def test_candidate_frame_conserves_population_and_binds_clusters() -> None:
    candidate = _candidate()
    validate_frame(candidate)
    assert candidate["status"] == "candidate"
    assert candidate["population"] == {
        "predecessor": 5,
        "included": 3,
        "excluded": 1,
        "unresolved": 1,
    }
    assert all("duplicate_cluster_id" in unit for unit in candidate["units"])
    assert candidate["rights_disposition"] == "not_inferred"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value["population"].update(predecessor=6), "population"),
        (lambda value: value["excluded_ids"].append("unit:1"), "disjoint"),
        (lambda value: value["units"].append(copy.deepcopy(value["units"][0])), "duplicate"),
        (lambda value: value.update(rights_eligible=True), "rights"),
        (lambda value: value.update(rights_disposition="eligible"), "rights"),
        (lambda value: value.update(annotation_authorized=True), "fields"),
    ],
)
def test_candidate_frame_rejects_imbalance_overlap_duplicates_and_rights_inference(
    mutation, message: str
) -> None:
    candidate = _candidate()
    mutation(candidate)
    _reseal(candidate, "frame_sha256")
    with pytest.raises(FrameContractError, match=message):
        validate_frame(candidate)


def test_finalization_is_structural_and_authorization_pinned(tmp_path) -> None:
    candidate = _candidate()
    immutable = finalize_frame(
        candidate,
        context=_frame_context(tmp_path),
        transition_authorization=_frame_approval(candidate),
    )
    validate_frame(immutable)
    assert immutable["status"] == "immutable"
    assert immutable["candidate_frame_sha256"] == candidate["frame_sha256"]
    assert (
        immutable["transition_authorization_sha256"]
        == _frame_approval(candidate)["artifact_sha256"]
    )
    assert immutable["rights_disposition"] == "not_inferred"


def test_finalization_rejects_non_candidate_or_invalid_authorization(tmp_path) -> None:
    candidate = _candidate()
    context = _frame_context(tmp_path)
    with pytest.raises(FrameContractError, match="approval"):
        finalize_frame(candidate, context=context, transition_authorization=None)
    with pytest.raises(FrameContractError, match=r"registered|self-pin"):
        finalize_frame(
            candidate,
            context=context,
            transition_authorization={**_frame_approval(candidate), "artifact_sha256": SHA_B},
        )
    immutable = finalize_frame(
        candidate,
        context=context,
        transition_authorization=_frame_approval(candidate),
    )
    with pytest.raises(FrameContractError, match="candidate"):
        finalize_frame(
            immutable,
            context=context,
            transition_authorization=_frame_approval(candidate),
        )


def test_frame_finalization_rejects_bare_unverified_approval_hash() -> None:
    with pytest.raises(FrameContractError, match="verified execution context"):
        finalize_frame(_candidate(), transition_authorization=_frame_approval(_candidate()))


def test_frame_finalization_rejects_registered_approval_for_unrelated_population(
    tmp_path: Path,
) -> None:
    approved = _candidate()
    context = _frame_context(tmp_path)
    unrelated = build_candidate_frame(
        frame_id="frame:unrelated",
        source_population_sha256=SHA_B,
        units=_units(),
        predecessor_count=5,
        excluded_ids=["excluded:1"],
        unresolved_ids=["unresolved:1"],
        duplicate_registry=build_duplicate_cluster_registry(_units()),
    )
    with pytest.raises(FrameContractError, match=r"candidate|population|approval"):
        finalize_frame(
            unrelated,
            context=context,
            transition_authorization=_frame_approval(approved),
        )


@pytest.mark.parametrize("field", ["candidate_frame_sha256", "source_population_sha256"])
def test_frame_approval_binds_exact_candidate_and_population(tmp_path: Path, field: str) -> None:
    candidate = _candidate()
    approval = _frame_approval(candidate)
    approval[field] = SHA_B
    approval = seal_record(approval, "artifact_sha256")
    context = build_context_fixture(
        tmp_path,
        extra_stages=(("frame", ("frame.finalize",)),),
        extra_referenced_artifacts=(
            ("frame-approval:test", approval["artifact_sha256"], "restricted_local"),
        ),
    ).context
    with pytest.raises(FrameContractError, match=r"candidate|population"):
        finalize_frame(candidate, context=context, transition_authorization=approval)


def test_candidate_builder_rejects_malformed_population_identities() -> None:
    units = _units()
    registry = build_duplicate_cluster_registry(units)
    malformed_ids: Any = [1]
    with pytest.raises(FrameContractError, match="excluded identity"):
        build_candidate_frame(
            frame_id="frame:au-test",
            source_population_sha256=SHA_A,
            units=units,
            predecessor_count=5,
            excluded_ids=malformed_ids,
            unresolved_ids=["unresolved:1"],
            duplicate_registry=registry,
        )


def test_population_counts_reject_booleans_even_when_equal_to_integers() -> None:
    unit = [_units()[0]]
    registry = build_duplicate_cluster_registry(unit)
    candidate = build_candidate_frame(
        frame_id="frame:one",
        source_population_sha256=SHA_A,
        units=unit,
        predecessor_count=1,
        excluded_ids=[],
        unresolved_ids=[],
        duplicate_registry=registry,
    )
    candidate["population"]["predecessor"] = True
    candidate["population"]["included"] = True
    _reseal(candidate, "frame_sha256")
    with pytest.raises(FrameContractError, match="nonnegative integers"):
        validate_frame(candidate)


def test_immutable_frame_rejects_candidate_or_authorization_tampering(tmp_path) -> None:
    immutable = finalize_frame(
        _candidate(),
        context=_frame_context(tmp_path),
        transition_authorization=_frame_approval(_candidate()),
    )
    immutable["candidate_frame_sha256"] = SHA_A
    _reseal(immutable, "frame_sha256")
    with pytest.raises(FrameContractError, match="candidate frame"):
        validate_frame(immutable)
