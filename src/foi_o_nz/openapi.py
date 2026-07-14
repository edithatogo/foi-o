"""OpenAPI contract generator for an eventual agent-facing FOI-O NZ service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json


def build_openapi_contract() -> dict[str, Any]:
    """Return a conservative OpenAPI 3.1 contract for bounded agent tools."""
    contract = {
        "openapi": "3.1.0",
        "info": {
            "title": "FOI-O NZ Agent Process API",
            "version": "0.8.1",
            "description": "Bounded process-support API. It exposes validation and drafting support, not autonomous OIA decision-making.",
        },
        "servers": [{"url": "http://localhost:8787", "description": "local development"}],
        "paths": {
            "/state/map": {
                "post": {
                    "summary": "Map an FYI/Alaveteli source state to a cautious FOI-O NZ state.",
                    "x-agent-boundary": "process-support-only",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StateMapRequest"}
                            }
                        },
                    },
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
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "schemas/json/agent-action.schema.json"}
                            }
                        },
                    },
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
            "/chunks/search": {
                "post": {
                    "summary": "Search deterministic chunk records for request context.",
                    "x-agent-boundary": "retrieval-only",
                    "responses": {"200": {"description": "Retrieval report"}},
                }
            },
            "/redactions/candidates": {
                "post": {
                    "summary": "Generate candidate sensitive-span review flags without redacting.",
                    "x-agent-boundary": "candidate-only-human-review-required",
                    "responses": {"200": {"description": "Redaction-candidate stream"}},
                }
            },
            "/agent-packs/build": {
                "post": {
                    "summary": "Build a request-scoped agent context pack with constraints and provenance.",
                    "x-agent-boundary": "context-packaging-only",
                    "responses": {"200": {"description": "Agent context pack"}},
                }
            },
            "/review-queue/build": {
                "post": {
                    "summary": "Build human-review tasks from risk, candidate redaction, and certification-boundary signals.",
                    "x-agent-boundary": "routing-only-no-decision",
                    "responses": {"200": {"description": "Review task stream"}},
                }
            },
            "/process/advice": {
                "post": {
                    "summary": "Generate preparatory process advice for one request.",
                    "x-agent-boundary": "advice-only-human-review-required",
                    "responses": {"200": {"description": "Process advice report"}},
                }
            },
            "/graphs/export": {
                "post": {
                    "summary": "Export a request/process graph for audit and agent navigation.",
                    "x-agent-boundary": "navigation-only",
                    "responses": {"200": {"description": "Graph export"}},
                }
            },
            "/attestations/artifacts": {
                "post": {
                    "summary": "Generate unsigned in-toto/SLSA-style provenance for artefacts.",
                    "x-agent-boundary": "integrity-metadata-only",
                    "responses": {"200": {"description": "Unsigned attestation"}},
                }
            },
            "/goldsets/sample": {
                "post": {
                    "summary": "Create deterministic human-review/evaluation samples.",
                    "x-agent-boundary": "evaluation-planning-only",
                    "responses": {"200": {"description": "Gold-set sample manifest"}},
                }
            },
            "/kernels/status": {
                "get": {
                    "summary": "Report Mojo/MAX kernel availability and fallback mode.",
                    "x-agent-boundary": "runtime-introspection-only",
                    "responses": {"200": {"description": "Native kernel status"}},
                }
            },
            "/kernels/conformance": {
                "post": {
                    "summary": "Run deterministic kernel conformance checks.",
                    "x-agent-boundary": "runtime-validation-only",
                    "responses": {"200": {"description": "Kernel conformance report"}},
                }
            },
            "/kernels/mojo-audit": {
                "post": {
                    "summary": "Statically audit Mojo declarations against fallback kernel operations.",
                    "x-agent-boundary": "runtime-validation-only",
                    "responses": {"200": {"description": "Static Mojo audit report"}},
                }
            },
            "/kernels/manifest": {
                "get": {
                    "summary": "Export the deterministic kernel operation manifest.",
                    "x-agent-boundary": "runtime-introspection-only",
                    "responses": {"200": {"description": "Kernel manifest"}},
                }
            },
            "/kernels/readiness": {
                "get": {
                    "summary": "Report Python fallback, static Mojo source, and native-release readiness.",
                    "x-agent-boundary": "runtime-introspection-only",
                    "responses": {"200": {"description": "Kernel readiness report"}},
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
    _add_agent_operation_metadata(contract)
    return contract


def _add_agent_operation_metadata(contract: dict[str, Any]) -> None:
    for methods in contract["paths"].values():
        for operation in methods.values():
            operation.setdefault("x-read-only", True)
            operation.setdefault("x-legal-effect", "none")
            operation.setdefault("x-machine-certification-allowed", False)
            operation.setdefault(
                "x-prohibited-follow-on-actions",
                [
                    "certify_release",
                    "certify_refusal",
                    "approve_redaction",
                    "approve_charge",
                    "certify_transfer",
                    "certify_extension",
                    "certify_complaint_or_review_outcome",
                ],
            )


def write_openapi_contract(output: Path) -> dict[str, Any]:
    """Write the OpenAPI contract as JSON."""
    contract = build_openapi_contract()
    write_json(output, contract)
    return {"ok": True, "output": str(output), "path_count": len(contract["paths"])}
