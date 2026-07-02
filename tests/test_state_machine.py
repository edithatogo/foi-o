from __future__ import annotations

from foi_o_nz.state_machine import (
    RequestState,
    can_transition,
    map_alaveteli_state,
    requires_human_certification,
)


def test_maps_known_alaveteli_state_cautiously() -> None:
    mapping = map_alaveteli_state("successful")

    assert mapping.normalised_state == RequestState.RELEASED_IN_FULL
    assert mapping.assertion_status == "inferred"
    assert mapping.confidence < 0.8


def test_maps_unknown_state_to_unknown() -> None:
    mapping = map_alaveteli_state("future_new_state")

    assert mapping.normalised_state == RequestState.UNKNOWN
    assert mapping.confidence == 0.0


def test_transition_guard_blocks_terminal_state() -> None:
    assert not can_transition(RequestState.REFUSED, RequestState.SEARCHING)
    assert can_transition(RequestState.SEARCHING, RequestState.DOCUMENTS_IDENTIFIED)


def test_human_certification_boundary() -> None:
    assert requires_human_certification("ReleaseMade")
    assert not requires_human_certification("SearchPlanDrafted")
