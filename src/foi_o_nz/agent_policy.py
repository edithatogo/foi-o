"""Rules-as-code guardrails for FOI-O NZ agent actions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from foi_o_nz.models import AgentAction

ActionType = Literal[
    "extract_events",
    "map_state",
    "calculate_deadline",
    "draft_search_plan",
    "draft_correspondence",
    "quality_check",
    "generate_reporting_metric",
    "flag_legal_issue",
]

ACTION_POLICY: dict[str, dict[str, Any]] = {
    "extract_events": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["certify_exemption", "approve_release"],
    },
    "map_state": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_state_as_legal_outcome"],
    },
    "calculate_deadline": {
        "legal_effect": "preparatory",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["certify_timeliness"],
    },
    "draft_search_plan": {
        "legal_effect": "preparatory",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["declare_search_adequate"],
    },
    "draft_correspondence": {
        "legal_effect": "preparatory",
        "requires_human_certification": True,
        "safety_class": "high",
        "prohibited_follow_on_actions": ["send_without_human_review"],
    },
    "quality_check": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": [],
    },
    "generate_reporting_metric": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["publish_without_reconciliation"],
    },
    "flag_legal_issue": {
        "legal_effect": "preparatory",
        "requires_human_certification": True,
        "safety_class": "high",
        "prohibited_follow_on_actions": ["apply_exemption_without_human_decision"],
    },
}


def classify_action(action_type: str) -> dict[str, Any]:
    """Return policy metadata for a supported action type."""
    try:
        return ACTION_POLICY[action_type].copy()
    except KeyError as exc:
        raise ValueError(f"unsupported agent action type: {action_type}") from exc


def build_agent_action(
    action_type: ActionType,
    *,
    agent_name: str = "foi-o-nz-agent",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    requested_at: datetime | None = None,
) -> AgentAction:
    """Build an AgentAction record from the policy table."""
    policy = classify_action(action_type)
    return AgentAction(
        action_id=f"foio-nz:agent-action:{uuid4()}",
        action_type=action_type,
        requested_at=requested_at or datetime.now(UTC),
        agent={"name": agent_name, "kind": "machine"},
        inputs=inputs or [],
        outputs=outputs or [],
        audit_trace=["generated_from_action_policy_v0.3"],
        **policy,
    )


def evaluate_agent_action(action: AgentAction | dict[str, Any]) -> dict[str, Any]:
    """Evaluate an action record against the current rules-as-code table."""
    parsed = action if isinstance(action, AgentAction) else AgentAction.model_validate(action)
    policy = classify_action(parsed.action_type)
    findings: list[dict[str, str]] = []
    for key in ["legal_effect", "requires_human_certification", "safety_class"]:
        if getattr(parsed, key) != policy[key]:
            findings.append(
                {
                    "severity": "error",
                    "code": f"policy_mismatch_{key}",
                    "message": f"{key} should be {policy[key]!r} for {parsed.action_type}",
                }
            )
    missing_prohibitions = sorted(
        set(policy["prohibited_follow_on_actions"]) - set(parsed.prohibited_follow_on_actions)
    )
    if missing_prohibitions:
        findings.append(
            {
                "severity": "warning",
                "code": "missing_prohibited_follow_on_actions",
                "message": ", ".join(missing_prohibitions),
            }
        )
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "action_id": parsed.action_id,
        "action_type": parsed.action_type,
        "legal_effect": parsed.legal_effect,
        "safety_class": parsed.safety_class,
        "requires_human_certification": parsed.requires_human_certification,
        "findings": findings,
    }
