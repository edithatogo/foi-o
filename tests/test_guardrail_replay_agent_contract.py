from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.agent_policy import build_agent_action, evaluate_agent_action
from foi_o_nz.replay import replay_guardrails


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def test_evaluate_agent_action_blocks_requested_prohibited_follow_on_action() -> None:
    action = build_agent_action("map_state").model_dump(mode="json")
    action["requested_follow_on_actions"] = ["treat_state_as_legal_outcome"]

    result = evaluate_agent_action(action)

    assert not result["ok"]
    assert any(
        finding["code"] == "prohibited_follow_on_action_requested" for finding in result["findings"]
    )


def test_replay_blocks_unsafe_requested_follow_on_action(tmp_path: Path) -> None:
    action = build_agent_action("map_state").model_dump(mode="json")
    action["requested_follow_on_actions"] = ["treat_state_as_legal_outcome"]
    actions_path = tmp_path / "actions.jsonl"
    _write_jsonl(actions_path, [action])

    report = replay_guardrails(actions_jsonl=actions_path)

    assert not report.ok
    finding = next(
        item for item in report.findings if item.code == "prohibited_follow_on_action_requested"
    )
    assert finding.severity == "error"
    assert finding.source_id == action["action_id"]
    assert "human review" in finding.message


def test_replay_preserves_safe_preparatory_action_provenance(tmp_path: Path) -> None:
    action = build_agent_action(
        "draft_search_plan",
        inputs=["foio-nz:request:123"],
        outputs=["foio-nz:search-plan:123"],
    ).model_dump(mode="json")
    action["audit_trace"].append("source:evidence-123")
    actions_path = tmp_path / "actions.jsonl"
    _write_jsonl(actions_path, [action])

    report = replay_guardrails(actions_jsonl=actions_path)

    assert report.ok
    finding = next(
        item for item in report.findings if item.code == "preparatory_action_context_retained"
    )
    assert finding.severity == "info"
    assert finding.source_id == action["action_id"]
    assert "source:evidence-123" in finding.message
    assert "preparatory" in finding.message
