"""MCP-oriented resource/prompt/tool bundle export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.tool_manifest import build_tool_manifest
from foi_o_nz.io import write_json


def build_mcp_bundle() -> dict[str, Any]:
    """Build a static MCP planning bundle with resources, prompts, and tools."""
    tool_manifest = build_tool_manifest()
    resources = [
        {
            "uri": "foio-nz://schemas/core-event",
            "name": "Core event JSON Schema",
            "mimeType": "application/schema+json",
            "path": "schemas/json/core-event.schema.json",
        },
        {
            "uri": "foio-nz://ontology/core",
            "name": "FOI-O NZ ontology seed",
            "mimeType": "text/turtle",
            "path": "ontology/foi-o-nz.ttl",
        },
        {
            "uri": "foio-nz://vocab/request-states",
            "name": "Request-state SKOS vocabulary",
            "mimeType": "text/turtle",
            "path": "vocab/request-states.skos.ttl",
        },
    ]
    prompts = [
        {
            "name": "extract_candidate_events",
            "description": "Extract candidate process events while preserving observed/inferred/asserted/certified status.",
            "arguments": [{"name": "source_text", "required": True}],
            "safety": "Outputs are candidates only; no legal decision certification.",
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
    ]
    return {
        "schema_version": "foi-o-nz.mcp-bundle.v0.1.0",
        "name": "foi-o-nz-mcp-planning-bundle",
        "resources": resources,
        "prompts": prompts,
        "tools": tool_manifest["tools"],
        "global_boundaries": tool_manifest["global_boundaries"],
    }


def write_mcp_bundle(output: Path) -> dict[str, Any]:
    """Write a static MCP planning bundle as JSON."""
    bundle = build_mcp_bundle()
    write_json(output, bundle)
    return {"ok": True, "output": str(output), "resource_count": len(bundle["resources"]), "prompt_count": len(bundle["prompts"]), "tool_count": len(bundle["tools"])}
