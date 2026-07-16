"""MCP-oriented resource/prompt/tool bundle export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json
from foi_o_nz.tool_manifest import build_tool_manifest


def build_mcp_bundle() -> dict[str, Any]:
    """Build a static MCP planning bundle with resources, prompts, and tools."""
    tool_manifest = build_tool_manifest()
    resources = [
        {
            "uri": "foio-nz://schemas/core-event",
            "name": "Global FOI-O core event JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/core-event.schema.json",
        },
        {
            "uri": "foio-nz://ontology/core",
            "name": "FOI-O ontology seed developed from the NZ reference profile",
            "mimeType": "text/turtle",
            "path": "ontology/foi-o-nz.ttl",
        },
        {
            "uri": "foio://schemas/jurisdiction-source-pack",
            "name": "Versioned jurisdiction source-pack JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/jurisdiction-source-pack.schema.json",
        },
        {
            "uri": "foio-nz://vocab/request-states",
            "name": "Request-state SKOS vocabulary",
            "mimeType": "text/turtle",
            "path": "vocab/request-states.skos.ttl",
        },
        {
            "uri": "foio-nz://kernels/status-schema",
            "name": "Native kernel status JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/native-kernel-status.schema.json",
        },
        {
            "uri": "foio-nz://kernels/mojo-audit-schema",
            "name": "Static Mojo audit JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/mojo-audit.schema.json",
        },
        {
            "uri": "foio-nz://kernels/kernel-manifest-schema",
            "name": "Kernel manifest JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/kernel-manifest.schema.json",
        },
        {
            "uri": "foio-nz://kernels/kernel-readiness-schema",
            "name": "Kernel readiness JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/kernel-readiness.schema.json",
        },
    ]
    prompts = [
        {
            "name": "extract_candidate_events",
            "description": "Extract candidate process events against an explicit versioned jurisdiction profile while preserving observed/inferred/asserted/certified status.",
            "arguments": [
                {"name": "source_text", "required": True},
                {"name": "jurisdiction", "required": True},
                {"name": "jurisdiction_profile", "required": True},
            ],
            "safety": "Outputs are candidates only; no legal decision certification or cross-jurisdiction fallback.",
        },
        {
            "name": "select_jurisdiction_profile",
            "description": "Validate an explicitly selected FOI-O jurisdiction profile and report its supported capabilities and promotion status.",
            "arguments": [
                {"name": "jurisdiction", "required": True},
                {"name": "profile_id", "required": True},
                {"name": "profile_version", "required": True},
            ],
            "safety": "Selection never implies legal approval; missing, incompatible, or unpromoted profiles fail closed or remain candidate-only.",
        },
        {
            "name": "draft_search_plan",
            "description": "Draft a search plan for a human FOI/OIA officer.",
            "arguments": [{"name": "agent_pack", "required": True}],
            "safety": "Preparatory only; cannot certify search adequacy.",
        },
        {
            "name": "review_redaction_candidates",
            "description": "Summarise candidate sensitive spans for human review using masked previews.",
            "arguments": [{"name": "redaction_candidates", "required": True}],
            "safety": "Candidate-only; cannot apply or approve redactions.",
        },
        {
            "name": "inspect_kernel_status",
            "description": "Inspect whether Mojo/MAX native kernels are available and whether Python fallback is active.",
            "arguments": [],
            "safety": "Runtime introspection only; does not authorise autonomous decisions.",
        },
        {
            "name": "inspect_kernel_readiness",
            "description": "Inspect static Mojo source readiness and remaining native-release blockers.",
            "arguments": [],
            "safety": "Runtime planning only; does not certify production readiness without native CI.",
        },
    ]
    return {
        "schema_version": "foi-o-nz.mcp-bundle.v0.1.0",
        "name": "foi-o-global-mcp-planning-bundle",
        "model_scope": "global_core_with_versioned_jurisdiction_profiles",
        "origin": "Developed from the New Zealand OIA profile and iterated through Australian Commonwealth and NSW adapters.",
        "jurisdiction_policy": {
            "explicit_profile_required": True,
            "cross_jurisdiction_fallback_allowed": False,
            "unpromoted_profile_outputs": "candidate_only",
            "current_iterations": ["NZ", "AU-CTH", "AU-NSW"],
        },
        "resources": resources,
        "prompts": prompts,
        "tools": tool_manifest["tools"],
        "global_boundaries": tool_manifest["global_boundaries"],
    }


def write_mcp_bundle(output: Path) -> dict[str, Any]:
    """Write a static MCP planning bundle as JSON."""
    bundle = build_mcp_bundle()
    write_json(output, bundle)
    return {
        "ok": True,
        "output": str(output),
        "resource_count": len(bundle["resources"]),
        "prompt_count": len(bundle["prompts"]),
        "tool_count": len(bundle["tools"]),
    }
