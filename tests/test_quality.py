from __future__ import annotations

from foi_o_nz.quality import assess_events


def test_quality_gate_flags_dispositive_without_certification_metadata() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:bad",
                "event_type": "ReleaseMade",
                "assertion_status": "inferred",
                "machine_generated": True,
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    )

    assert not result["ok"]
    assert result["error_count"] >= 1


def test_quality_gate_accepts_observed_event() -> None:
    result = assess_events(
        [
            {
                "event_id": "foio-nz:event:ok",
                "event_type": "RequestObserved",
                "assertion_status": "observed",
                "machine_generated": True,
                "generator": {"system": "foi-o-nz"},
                "requires_human_certification": False,
                "evidence": [{"evidence_id": "e1"}],
            }
        ]
    )

    assert result["ok"]
