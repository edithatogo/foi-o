"""Property-based tests for the OIA lifecycle state machine (trial: Hypothesis).

Invariants under test:
- ``can_transition`` permits self-loops and exactly the ALLOWED_TRANSITIONS
  entries whose source is not terminal;
- terminal states emit no transitions to other states;
- ``audit_transitions`` reports ok on any legal transition walk, and flags an
  unexpected_transition finding when an illegal transition is injected.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from foi_o_nz.state_machine import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    RequestState,
    can_transition,
)
from foi_o_nz.transitions import audit_transitions

states = st.sampled_from(list(RequestState))


@st.composite
def _walk_strategy(draw: st.DrawFn) -> list[RequestState]:
    """Generate random walks where every consecutive pair is a legal transition."""
    chain = [draw(states)]
    for _ in range(draw(st.integers(min_value=0, max_value=20))):
        current = chain[-1]
        successors = [
            t for t in ALLOWED_TRANSITIONS.get(current, set()) if can_transition(current, t)
        ]
        if not successors:
            break
        chain.append(draw(st.sampled_from(successors)))
    return chain


_illegal_pairs = [
    (s, t) for s in RequestState for t in RequestState if s != t and not can_transition(s, t)
]
illegal_pairs = st.sampled_from(_illegal_pairs)


@settings(max_examples=300, deadline=None)
@given(source=states, target=states)
def test_can_transition_agrees_with_allowed_transitions(
    source: RequestState, target: RequestState
) -> None:
    # Documented semantics: self-loops are always permitted (idempotent
    # re-statements of the same state), and terminal states emit no
    # transitions to other states even where ALLOWED_TRANSITIONS lists a key.
    expected = source == target or (
        target in ALLOWED_TRANSITIONS.get(source, set()) and source not in TERMINAL_STATES
    )
    assert can_transition(source, target) == expected


@settings(max_examples=300, deadline=None)
@given(source=states, target=states)
def test_terminal_states_emit_no_transitions(source: RequestState, target: RequestState) -> None:
    if source in TERMINAL_STATES and source != target:
        assert not can_transition(source, target)


def _events_for(request_id: str, chain: list[RequestState]) -> list[dict[str, object]]:
    return [
        {
            "event_id": f"evt-{request_id}-{index}",
            "request_id": request_id,
            "event_time": f"2026-01-01T00:00:{index:02d}Z",
            "lifecycle_state_after": state.value,
        }
        for index, state in enumerate(chain)
    ]


@settings(max_examples=200, deadline=None)
@given(
    request_id=st.text(min_size=1, max_size=12, alphabet="abcdefgh123456"), chain=_walk_strategy()
)
def test_audit_ok_for_purely_legal_chains(request_id: str, chain: list[RequestState]) -> None:
    report = audit_transitions(_events_for(request_id, chain))
    assert report["ok"], report["findings"]


@settings(max_examples=200, deadline=None)
@given(
    request_id=st.text(min_size=1, max_size=12, alphabet="abcdefgh123456"),
    illegal=illegal_pairs,
)
def test_audit_flags_illegal_transition(
    request_id: str,
    illegal: tuple[RequestState, RequestState],
) -> None:
    report = audit_transitions(_events_for(request_id, [illegal[0], illegal[1]]))
    assert not report["ok"]
    assert report["finding_count"] >= 1
    assert any(f["code"] == "unexpected_transition" for f in report["findings"])
