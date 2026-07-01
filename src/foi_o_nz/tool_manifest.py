"""Agent tool/capability manifest generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.agent_policy import ACTION_POLICY
from foi_o_nz.io import write_json


def build_tool_manifest() -> dict[str, Any]:
    """Return a bounded tool manifest for MCP/OpenAPI/agent runtime planning."""
    tools: list[dict[str, Any]] = []
    for action_type, policy in sorted(ACTION_POLICY.items()):
        tools.append(
            {
                "name": action_type,
                "description": _description_for_action(action_type),
                "legal_effect": policy["legal_effect"],
                "safety_class": policy["safety_class"],
                "requires_human_certification": policy["requires_human_certification"],
                "prohibited_follow_on_actions": policy["prohibited_follow_on_actions"],
                "machine_certification_allowed": False,
            }
        )
    return {
        "schema_version": "foi-o-nz.tool-manifest.v0.1.0",
        "name": "foi-o-nz-agent-tools",
        "description": "Bounded tools for process support, validation, and evidence preparation. No tool certifies an OIA decision.",
        "tools": tools,
        "global_boundaries": [
            "No autonomous release/refusal/redaction/charge/extension/transfer certification.",
            "Observed/inferred/asserted/certified status must be preserved.",
            "Machine-generated outputs must remain reviewable and auditable.",
        ],
    }


def _description_for_action(action_type: str) -> str:
    descriptions = {
        "extract_events": "Extract candidate process events from source records.",
        "map_state": "Map source platform states to cautious FOI-O NZ states.",
        "calculate_deadline": "Calculate indicative process deadlines for operator review.",
        "draft_search_plan": "Draft a search plan for human review.",
        "draft_correspondence": "Draft correspondence text that must be reviewed before sending.",
        "quality_check": "Run validation and quality-gate checks.",
        "generate_reporting_metric": "Generate draft reporting metrics for reconciliation.",
        "flag_legal_issue": "Flag possible legal/process issues for human review.",
    }
    return descriptions.get(action_type, "Bounded FOI-O NZ tool action.")


def write_tool_manifest(output: Path) -> dict[str, Any]:
    """Write the bounded tool manifest."""
    manifest = build_tool_manifest()
    write_json(output, manifest)
    return {"ok": True, "output": str(output), "tool_count": len(manifest["tools"])}
