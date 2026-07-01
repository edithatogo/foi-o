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
    tools.extend(
        [
            {
                "name": "search_chunks",
                "description": "Retrieve request-scoped context from deterministic text chunks.",
                "legal_effect": "none",
                "safety_class": "retrieval_only",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["certify_decision", "release_information"],
                "machine_certification_allowed": False,
            },
            {
                "name": "propose_redaction_candidates",
                "description": "Flag candidate sensitive spans with hashed/masked previews for human review.",
                "legal_effect": "none",
                "safety_class": "privacy_triage",
                "requires_human_certification": True,
                "prohibited_follow_on_actions": ["apply_redaction", "withhold_information"],
                "machine_certification_allowed": False,
            },
            {
                "name": "build_agent_pack",
                "description": "Assemble request-scoped context packs with constraints and provenance.",
                "legal_effect": "none",
                "safety_class": "context_packaging",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["certify_decision"],
                "machine_certification_allowed": False,
            },
            {
                "name": "kernel_status",
                "description": "Report Mojo/MAX kernel availability and Python fallback mode.",
                "legal_effect": "none",
                "safety_class": "runtime_introspection",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["treat_tool_availability_as_decision_authority"],
                "machine_certification_allowed": False,
            },

            {
                "name": "mojo_audit",
                "description": "Statically audit Mojo source declarations against fallback kernel operations.",
                "legal_effect": "none",
                "safety_class": "runtime_validation",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["treat_static_audit_as_native_release_certification"],
                "machine_certification_allowed": False,
            },
            {
                "name": "export_kernel_manifest",
                "description": "Export deterministic kernel operation metadata for native/fallback parity planning.",
                "legal_effect": "none",
                "safety_class": "runtime_introspection",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["treat_manifest_as_decision_authority"],
                "machine_certification_allowed": False,
            },
            {
                "name": "kernel_readiness",
                "description": "Report remaining blockers before Mojo-native kernel release certification.",
                "legal_effect": "none",
                "safety_class": "runtime_validation",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["skip_native_mojo_ci"],
                "machine_certification_allowed": False,
            },
            {
                "name": "kernel_conformance",
                "description": "Run deterministic Mojo/Python fallback kernel conformance checks.",
                "legal_effect": "none",
                "safety_class": "runtime_validation",
                "requires_human_certification": False,
                "prohibited_follow_on_actions": ["treat_test_pass_as_operational_authorisation"],
                "machine_certification_allowed": False,
            },
        ]
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
        "search_chunks": "Retrieve process context from deterministic chunks.",
        "propose_redaction_candidates": "Flag candidate sensitive spans for human review without redacting.",
        "build_agent_pack": "Assemble request-scoped context packs with provenance and constraints.",
        "diff_streams": "Compare artefact streams by stable IDs and canonical hashes.",
        "build_review_queue": "Route candidate risks and certification boundaries to human review tasks.",
        "build_process_advice": "Generate preparatory next-step advice without deciding outcomes.",
        "export_graph": "Export request/event/chunk/risk relationships as a graph artefact.",
        "attest_artifacts": "Generate unsigned provenance attestations for artefact integrity workflows.",
        "sample_goldset": "Create deterministic evaluation/annotation samples with bounded claims.",
        "export_annotation_tasks": "Export neutral or Label Studio review tasks for human-in-the-loop labelling.",
        "kernel_status": "Report Mojo/MAX native-kernel availability and fallback mode.",
        "kernel_eval": "Evaluate one deterministic kernel operation without certifying legal outcomes.",
        "kernel_conformance": "Run deterministic kernel conformance checks across Mojo and fallback semantics.",
        "kernel_readiness": "Report remaining blockers before Mojo-native release certification.",
        "export_kernel_manifest": "Export deterministic kernel operation metadata for native/fallback parity planning.",
        "mojo_audit": "Statically audit Mojo source declarations against fallback kernel operations.",
    }
    return descriptions.get(action_type, "Bounded FOI-O NZ tool action.")


def write_tool_manifest(output: Path) -> dict[str, Any]:
    """Write the bounded tool manifest."""
    manifest = build_tool_manifest()
    write_json(output, manifest)
    return {"ok": True, "output": str(output), "tool_count": len(manifest["tools"])}
