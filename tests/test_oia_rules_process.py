"""Tests for oia_rules process bridge into LegalClock / events."""

from __future__ import annotations

from datetime import UTC, datetime

from foi_o_nz.normalise import build_observed_events, build_request_profile
from foi_o_nz.oia_rules.process import (
    OIA_RULES_CALCULATION_METHOD,
    legal_clock_from_oia_rules,
)


def test_legal_clock_from_oia_rules_sets_method_and_deadlines() -> None:
    received = datetime(2026, 6, 1, tzinfo=UTC)
    clock = legal_clock_from_oia_rules(received)
    assert clock is not None
    assert clock.calculation_method == OIA_RULES_CALCULATION_METHOD
    assert clock.decision_due_date is not None
    assert clock.transfer_due_date is not None
    assert clock.transfer_due_date <= clock.decision_due_date
    assert any("oia_rules_dispatch" in w for w in clock.warnings)


def test_legal_clock_none_without_receipt() -> None:
    assert legal_clock_from_oia_rules(None) is None


def test_normalise_uses_oia_rules_clock() -> None:
    record = {
        "request_id": 123,
        "url_title": "123_test_request",
        "title": "Test request",
        "authority": "Test Ministry",
        "state": "partially_successful",
        "first_sent": "2026-06-01T00:00:00Z",
        "last_updated": "2026-06-03T00:00:00Z",
        "content_sha256": "b" * 64,
        "html_captured": True,
        "attachments": [],
        "warc_record_ids": ["warc:1"],
    }
    profile = build_request_profile(record)
    assert profile.legal_clock is not None
    assert profile.legal_clock.calculation_method == OIA_RULES_CALCULATION_METHOD
    events = build_observed_events(profile)
    deadline = next(e for e in events if e.event_type == "DeadlineCalculated")
    assert "oia_rules_dispatch" in deadline.quality_flags
    assert "indicative_deadline_not_certified" in deadline.quality_flags
