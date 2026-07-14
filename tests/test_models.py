from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from foi_o_nz.models import Actor, CoreEvent, EvidenceRef, RequestRef


def _base_event(**overrides: object) -> dict[str, Any]:
    data: dict[str, Any] = {
        "event_id": "foio-nz:event:test",
        "event_type": "RequestObserved",
        "event_time": datetime(2026, 7, 1, tzinfo=UTC),
        "request_ref": RequestRef(source_system="fyi-archive-nz", source_request_id="1"),
        "source_system": "fyi-archive-nz",
        "actor": Actor(role="system"),
        "assertion_status": "observed",
        "confidence": 1.0,
        "machine_generated": True,
        "generator": {"system": "foi-o-nz", "software_version": "0.1.0"},
        "requires_human_certification": False,
        "evidence": [EvidenceRef(evidence_id="e1", evidence_type="archive_manifest")],
    }
    data.update(overrides)
    return data


def test_core_event_model_accepts_observed_request_event() -> None:
    event = CoreEvent(**_base_event())

    assert event.event_type == "RequestObserved"
    assert event.assertion_status == "observed"


def test_dispositive_event_requires_human_certification() -> None:
    with pytest.raises(ValidationError):
        CoreEvent(**_base_event(event_type="ReleaseMade", requires_human_certification=False))


def test_certified_assertion_requires_positive_certification() -> None:
    with pytest.raises(ValidationError):
        CoreEvent(**_base_event(assertion_status="certified", requires_human_certification=True))
