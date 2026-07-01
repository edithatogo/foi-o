from __future__ import annotations

from foi_o_nz.agent_policy import build_agent_action, evaluate_agent_action


def test_build_agent_action_template() -> None:
    action = build_agent_action("map_state", agent_name="tester")
    assert action.agent["name"] == "tester"
    assert action.legal_effect == "none"
    assert action.safety_class == "low"


def test_evaluate_agent_action_ok() -> None:
    action = build_agent_action("draft_correspondence")
    result = evaluate_agent_action(action)
    assert result["ok"]
    assert result["requires_human_certification"] is True


def test_evaluate_agent_action_flags_policy_mismatch() -> None:
    action = build_agent_action("map_state")
    data = action.model_dump(mode="json")
    data["legal_effect"] = "preparatory"
    result = evaluate_agent_action(data)
    assert not result["ok"]
    assert result["findings"][0]["code"] == "policy_mismatch_legal_effect"
