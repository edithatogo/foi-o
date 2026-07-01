"""OpenAPI contract generator for an eventual agent-facing FOI-O NZ service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json


def build_openapi_contract() -> dict[str, Any]:
    """Return a conservative OpenAPI 3.1 contract for bounded agent tools."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "FOI-O NZ Agent Process API",
            "version": "0.4.0",
            "description": "Bounded process-support API. It exposes validation and drafting support, not autonomous OIA decision-making.",
        },
        "servers": [{"url": "http://localhost:8787", "description": "local development"}],
        "paths": {
            "/state/map": {
                "post": {
                    "summary": "Map an FYI/Alaveteli source state to a cautious FOI-O NZ state.",
                    "x-agent-boundary": "process-support-only",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StateMapRequest"}}}},
                    "responses": {"200": {"description": "State mapping"}},
                }
            },
            "/events/quality-gate": {
                "post": {
                    "summary": "Assess event-stream provenance and certification-boundary risks.",
                    "x-agent-boundary": "quality-assurance-only",
                    "responses": {"200": {"description": "Quality report"}},
                }
            },
            "/agent-actions/evaluate": {
                "post": {
                    "summary": "Evaluate whether a proposed agent action stays within policy.",
                    "x-agent-boundary": "guardrail-enforcement",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "schemas/json/agent-action.schema.json"}}}},
                    "responses": {"200": {"description": "Policy decision"}},
                }
            },
            "/ledgers/verify": {
                "post": {
                    "summary": "Verify a tamper-evident JSONL ledger against a source stream.",
                    "x-agent-boundary": "evidence-integrity-only",
                    "responses": {"200": {"description": "Ledger verification result"}},
                }
            },
        },
        "components": {
            "schemas": {
                "StateMapRequest": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source_state"],
                    "properties": {"source_state": {"type": "string"}},
                }
            }
        },
    }


def write_openapi_contract(output: Path) -> dict[str, Any]:
    """Write the OpenAPI contract as JSON."""
    contract = build_openapi_contract()
    write_json(output, contract)
    return {"ok": True, "output": str(output), "path_count": len(contract["paths"])}
