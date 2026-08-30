"""Property-based tests for the archive retry policy (trial: Hypothesis).

Invariants under test:
- backoff is non-negative, monotonically non-decreasing in attempt, and capped;
- ``is_retryable`` exactly partitions the configured sets;
- retryable and terminal status code sets never overlap (fail-closed);
- default construction is safe: no terminal status is retryable.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from foi_o_nz.archive_adapters import RetryPolicy

status_codes = st.integers(min_value=100, max_value=599)
positive = st.floats(min_value=0.1, max_value=120.0, allow_nan=False, allow_infinity=False)
multiplier = st.floats(min_value=1.0, max_value=4.0, allow_nan=False, allow_infinity=False)


@settings(max_examples=200, deadline=None)
@given(attempt=st.integers(min_value=0, max_value=200))
def test_backoff_is_non_negative_and_capped(attempt: int) -> None:
    policy = RetryPolicy()
    delay = policy.compute_backoff(attempt)
    assert delay >= 0
    assert delay <= policy.max_delay_seconds


@settings(max_examples=200, deadline=None)
@given(
    attempt_a=st.integers(min_value=0, max_value=60),
    attempt_b=st.integers(min_value=0, max_value=60),
)
def test_backoff_is_monotonic_in_attempt(attempt_a: int, attempt_b: int) -> None:
    policy = RetryPolicy()
    if attempt_a <= attempt_b:
        assert policy.compute_backoff(attempt_a) <= policy.compute_backoff(attempt_b)
    else:
        assert policy.compute_backoff(attempt_a) >= policy.compute_backoff(attempt_b)


@settings(max_examples=200, deadline=None)
@given(code=status_codes)
def test_is_retryable_matches_configured_sets(code: int) -> None:
    policy = RetryPolicy()
    assert policy.is_retryable(code) == (code in policy.retryable_status_codes)
    if code in policy.terminal_status_codes:
        assert not policy.is_retryable(code)


@settings(max_examples=100, deadline=None)
@given(
    retryable=st.sets(status_codes, max_size=20),
    terminal=st.sets(status_codes, max_size=20),
)
def test_terminal_codes_are_never_retryable(retryable: set[int], terminal: set[int]) -> None:
    policy = RetryPolicy(
        retryable_status_codes=retryable - terminal,
        terminal_status_codes=terminal,
    )
    for code in terminal:
        assert not policy.is_retryable(code)


@settings(max_examples=50, deadline=None)
@given(base=positive, mult=multiplier, cap=positive)
def test_capped_policy_never_exceeds_cap(base: float, mult: float, cap: float) -> None:
    policy = RetryPolicy(
        base_delay_seconds=base,
        max_delay_seconds=max(base, cap),
        backoff_multiplier=mult,
    )
    for attempt in range(1, 40):
        assert policy.compute_backoff(attempt) <= policy.max_delay_seconds + 1e-9
