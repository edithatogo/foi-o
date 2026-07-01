from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from foi_o_nz.models import AgentAction


def test_agent_action_accepts_schema_example_shape() -> None:
    action = AgentAction(
        action_id="agent-action:test",
        action_type="draft_search_plan",
        requested_at=datetime(2026, 7, 1, tzinfo=UTC),
        agent={"name": "foi-o-nz-process-agent", "version": "0.2.0"},
        inputs=["foio-nz:request:1"],
        outputs=["draft-search-plan:1"],
        legal_effect="preparatory",
        requires_human_certification=True,
        safety_class="medium",
        prohibited_follow_on_actions=["certify_search_complete"],
        audit_trace=["schema:agent-action.v0.1.0"],
    )

    assert action.action_type == "draft_search_plan"


def test_agent_action_prohibited_boundary_is_consistent() -> None:
    with pytest.raises(ValidationError):
        AgentAction(
            action_id="agent-action:bad",
            action_type="quality_check",
            requested_at=datetime(2026, 7, 1, tzinfo=UTC),
            agent={"name": "agent"},
            legal_effect="preparatory",
            requires_human_certification=True,
            safety_class="prohibited",
        )
