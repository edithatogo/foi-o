from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.analytics import summarise_events_jsonl


def test_summarise_events_jsonl(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event_type": "RequestObserved",
                "assertion_status": "observed",
                "confidence": 1.0,
                "requires_human_certification": False,
                "machine_generated": True,
                "quality_flags": ["example"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = summarise_events_jsonl(events)

    assert summary["event_count"] == 1
    assert summary["event_type_counts"]["RequestObserved"] == 1
    assert summary["quality_flag_counts"]["example"] == 1
