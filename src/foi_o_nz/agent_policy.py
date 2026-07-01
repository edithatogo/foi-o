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
    "search_chunks",
    "propose_redaction_candidates",
    "build_agent_pack",
    "diff_streams",
    "build_review_queue",
    "build_process_advice",
    "export_graph",
    "attest_artifacts",
    "sample_goldset",
    "export_annotation_tasks",
    "cas_manifest",
    "materialise_cas",
    "lineage_graph",
    "trace_artifacts",
    "build_goldset_tasks",
    "replay_guardrails",
    "export_table_contracts",
    "materialise_oci",
    "export_mcp_bundle",
    "kernel_status",
    "kernel_eval",
    "kernel_conformance",
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
    "search_chunks": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_retrieval_as_decision_evidence_without_review"],
    },
    "propose_redaction_candidates": {
        "legal_effect": "none",
        "requires_human_certification": True,
        "safety_class": "high",
        "prohibited_follow_on_actions": ["apply_redaction_without_human_decision"],
    },
    "build_agent_pack": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["certify_decision_from_pack"],
    },
    "diff_streams": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["publish_incremental_change_without_reconciliation"],
    },
    "build_review_queue": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["treat_queue_as_legal_decision"],
    },
    "build_process_advice": {
        "legal_effect": "preparatory",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["execute_advice_without_review"],
    },
    "export_graph": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_graph_edges_as_certified_fact"],
    },
    "attest_artifacts": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_unsigned_attestation_as_signed_provenance"],
    },
    "sample_goldset": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["treat_sample_as_representative_without_review"],
    },
    "export_annotation_tasks": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["record_decision_in_annotation_task"],
    },
    "cas_manifest": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_hash_manifest_as_legal_certification"],
    },
    "materialise_cas": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["publish_private_objects_without_review"],
    },
    "lineage_graph": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["treat_heuristic_lineage_as_certified_provenance"],
    },
    "trace_artifacts": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["infer_user_consent_from_trace"],
    },
    "build_goldset_tasks": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["record_decision_in_goldset_task"],
    },
    "replay_guardrails": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_replay_pass_as_legal_approval"],
    },
    "export_table_contracts": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_table_contract_as_authoritative_case_record"],
    },
    "materialise_oci": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["push_unsigned_artifact_as_trusted_release"],
    },
    "export_mcp_bundle": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "medium",
        "prohibited_follow_on_actions": ["grant_runtime_tool_access_without_operator_policy"],
    },
    "kernel_status": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_tool_availability_as_decision_authority"],
    },
    "kernel_eval": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_kernel_result_as_certified_legal_outcome"],
    },
    "kernel_conformance": {
        "legal_effect": "none",
        "requires_human_certification": False,
        "safety_class": "low",
        "prohibited_follow_on_actions": ["treat_test_pass_as_operational_authorisation"],
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
        audit_trace=["generated_from_action_policy_v0.7"],
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
