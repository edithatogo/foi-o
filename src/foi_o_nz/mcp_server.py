"""Optional MCP server exposing bounded FOI-O NZ tools.

The module imports FastMCP lazily so the core package stays usable without the
optional MCP extra. Every tool is preparatory or validation-only; none can
certify legal outcomes.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from foi_o_nz.io import loads_json
from foi_o_nz.quality import assess_events_jsonl
from foi_o_nz.state_machine import map_alaveteli_state
from foi_o_nz.validation import validate_json_schema, validate_jsonl_schema

MCP_UNAVAILABLE_MESSAGE = (
    "fastmcp is required to run the FOI-O NZ MCP server; install foi-o-nz[mcp]. "
    "Runtime startup is fail-closed and no fallback server is exposed without FastMCP."
)
PROHIBITED_FOLLOW_ON_ACTIONS = [
    "certify_release",
    "certify_refusal",
    "approve_redaction",
    "approve_charge",
    "certify_transfer",
    "certify_extension",
    "certify_complaint_or_review_outcome",
]
SCHEMA_ROOT = Path("schemas/json")


def _load_fastmcp() -> type[Any]:
    """Load FastMCP only when the optional MCP runtime is requested."""
    from fastmcp import FastMCP  # type: ignore[import-not-found]

    return FastMCP


def mcp_runtime_status() -> dict[str, Any]:
    """Return explicit optional-runtime status for operators and tests."""
    try:
        _load_fastmcp()
    except ModuleNotFoundError:
        return {
            "ok": False,
            "mode": "degraded",
            "read_only": True,
            "message": MCP_UNAVAILABLE_MESSAGE,
        }
    return {
        "ok": True,
        "mode": "fastmcp",
        "read_only": True,
        "message": "FastMCP available; FOI-O NZ tools remain read-only and preparatory.",
    }


def map_state_tool(source_state: str) -> dict[str, Any]:
    """Map an FYI/Alaveteli state without certifying an OIA outcome."""
    mapping = map_alaveteli_state(source_state)
    return {
        "source_state": mapping.source_state,
        "normalised_state": mapping.normalised_state.value,
        "confidence": mapping.confidence,
        "assertion_status": mapping.assertion_status,
        "notes": mapping.notes,
        "legal_effect": "none",
        "read_only": True,
    }


def validate_json_tool(
    instance_path: str, schema_path: str, *, fixture_root: Path | str = Path()
) -> dict[str, Any]:
    """Validate one fixture JSON file against a schema in read-only mode."""
    result = validate_json_schema(
        _resolve_fixture_path(instance_path, fixture_root=fixture_root),
        _resolve_fixture_path(schema_path, fixture_root=fixture_root),
    )
    return {
        "ok": result.ok,
        "errors": list(result.errors),
        "legal_effect": "none",
        "read_only": True,
    }


def validate_jsonl_tool(
    instance_path: str, schema_path: str, *, fixture_root: Path | str = Path()
) -> dict[str, Any]:
    """Validate one fixture JSONL file against a schema in read-only mode."""
    result = validate_jsonl_schema(
        _resolve_fixture_path(instance_path, fixture_root=fixture_root),
        _resolve_fixture_path(schema_path, fixture_root=fixture_root),
    )
    return {
        "ok": result.ok,
        "errors": list(result.errors),
        "legal_effect": "none",
        "read_only": True,
    }


def quality_gate_tool(
    events_jsonl_path: str, *, fixture_root: Path | str = Path()
) -> dict[str, Any]:
    """Run read-only event-stream metadata and provenance quality checks."""
    result = assess_events_jsonl(
        _resolve_fixture_path(events_jsonl_path, fixture_root=fixture_root)
    )
    result["legal_effect"] = "none"
    result["read_only"] = True
    return result


def schema_resource_text(schema_name: str, *, schema_root: Path | str = SCHEMA_ROOT) -> str:
    """Return one committed JSON Schema as text."""
    path = _resolve_committed_schema(schema_name, schema_root=schema_root)
    data = loads_json(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, sort_keys=True)


def state_mapping_context(source_state: str) -> str:
    """Return bounded prompt context for state mapping."""
    mapping = map_alaveteli_state(source_state)
    return (
        f"Source state: {mapping.source_state}\n"
        f"Candidate FOI-O NZ state: {mapping.normalised_state.value}\n"
        f"Assertion status: {mapping.assertion_status}\n"
        f"Confidence: {mapping.confidence}\n"
        f"Notes: {mapping.notes}\n"
        "Boundary: this context cannot certify release, refusal, redaction, charging, "
        "transfer, extension, complaint, or review outcomes."
    )


def create_server(
    *, fixture_root: Path | str = Path(), fastmcp_cls: type[Any] | None = None
) -> Any:
    """Create a FastMCP server instance."""
    if fastmcp_cls is None:
        try:
            fastmcp_cls = _load_fastmcp()
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(MCP_UNAVAILABLE_MESSAGE) from exc

    root = Path(fixture_root)
    mcp = fastmcp_cls("foi-o-nz")

    @mcp.tool(
        **_decorator_kwargs(
            mcp.tool,
            _runtime_metadata("Map a source platform state to a cautious FOI-O NZ process state."),
        )
    )
    def map_state(source_state: str) -> dict[str, Any]:
        """Map an FYI/Alaveteli state to FOI-O NZ lifecycle vocabulary."""
        return map_state_tool(source_state)

    @mcp.tool(
        **_decorator_kwargs(
            mcp.tool,
            _runtime_metadata("Validate one fixture JSON file against a committed JSON Schema."),
        )
    )
    def validate_json(instance_path: str, schema_path: str) -> dict[str, Any]:
        """Validate a JSON file against a JSON Schema."""
        return validate_json_tool(instance_path, schema_path, fixture_root=root)

    @mcp.tool(
        **_decorator_kwargs(
            mcp.tool,
            _runtime_metadata("Validate one fixture JSONL stream against a committed JSON Schema."),
        )
    )
    def validate_jsonl(instance_path: str, schema_path: str) -> dict[str, Any]:
        """Validate a JSONL file against a JSON Schema."""
        return validate_jsonl_tool(instance_path, schema_path, fixture_root=root)

    @mcp.tool(
        **_decorator_kwargs(
            mcp.tool,
            _runtime_metadata(
                "Assess event-stream metadata, provenance, and human-boundary risks."
            ),
        )
    )
    def quality_gate(events_jsonl_path: str) -> dict[str, Any]:
        """Run event-stream metadata and provenance gates."""
        return quality_gate_tool(events_jsonl_path, fixture_root=root)

    @mcp.resource(
        "foio://schema/{schema_name}",
        **_decorator_kwargs(
            mcp.resource,
            _runtime_metadata("Return one committed FOI-O NZ JSON Schema as text."),
            name="schema_resource",
            resource=True,
        ),
    )
    def schema_resource(schema_name: str) -> str:
        """Return one committed JSON Schema as text."""
        return schema_resource_text(schema_name, schema_root=root / SCHEMA_ROOT)

    if hasattr(mcp, "prompt"):

        @mcp.prompt(
            **_decorator_kwargs(
                mcp.prompt,
                _runtime_metadata("Provide bounded prompt context for cautious state mapping."),
                name="state_mapping_context",
            )
        )
        def state_mapping_context_prompt(source_state: str) -> str:
            """Build bounded prompt context for one source state."""
            return state_mapping_context(source_state)

        if hasattr(mcp, "prompts") and "state_mapping_context_prompt" in mcp.prompts:
            mcp.prompts["state_mapping_context"] = mcp.prompts.pop("state_mapping_context_prompt")

    return mcp


def run_server() -> None:
    """Run the optional MCP server."""
    server = create_server()
    server.run()


def _runtime_metadata(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "legal_effect": "none",
        "read_only": True,
        "machine_certification_allowed": False,
        "prohibited_follow_on_actions": PROHIBITED_FOLLOW_ON_ACTIONS,
    }


def _decorator_kwargs(
    decorator: Any,
    metadata: dict[str, Any],
    *,
    name: str | None = None,
    resource: bool = False,
) -> dict[str, Any]:
    """Adapt local descriptor metadata to fake or real FastMCP decorators."""
    signature = inspect.signature(decorator)
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
        return metadata
    common = {
        "description": metadata["description"],
        "meta": metadata,
    }
    if name is not None and "name" in signature.parameters:
        common["name"] = name
    if resource:
        return {**common, "mime_type": "application/schema+json"}
    if "annotations" in signature.parameters:
        common["annotations"] = {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    return common


def _resolve_fixture_path(path: str, *, fixture_root: Path | str) -> Path:
    root = Path(fixture_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError(f"fixture path must stay inside {root}: {path}")
    if not resolved.is_file():
        raise ValueError(f"fixture path does not exist: {path}")
    return resolved


def _resolve_committed_schema(schema_name: str, *, schema_root: Path | str) -> Path:
    candidate = Path(schema_name)
    if candidate.name != schema_name or not schema_name.endswith(".schema.json"):
        raise ValueError("schema resource must reference a committed JSON Schema filename")
    root = Path(schema_root).resolve()
    resolved = (root / candidate).resolve()
    if root != resolved.parent or not resolved.is_file():
        raise ValueError("schema resource must reference a committed JSON Schema filename")
    return resolved
