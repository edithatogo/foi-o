"""Optional MCP server exposing bounded FOI-O NZ tools.

The module imports FastMCP lazily so the core package stays usable without the
optional MCP extra. Every tool is preparatory or validation-only; none can
certify legal outcomes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from foi_o_nz.io import loads_json, write_json
from foi_o_nz.quality import assess_events_jsonl
from foi_o_nz.state_machine import map_alaveteli_state
from foi_o_nz.validation import validate_json_schema, validate_jsonl_schema


def create_server() -> Any:
    """Create a FastMCP server instance."""
    try:
        from fastmcp import FastMCP  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("fastmcp is required: install foi-o-nz[mcp]") from exc

    mcp = FastMCP("foi-o-nz")

    @mcp.tool()
    def map_state(source_state: str) -> dict[str, Any]:
        """Map an FYI/Alaveteli state to FOI-O NZ lifecycle vocabulary."""
        mapping = map_alaveteli_state(source_state)
        return {
            "source_state": mapping.source_state,
            "normalised_state": mapping.normalised_state.value,
            "confidence": mapping.confidence,
            "assertion_status": mapping.assertion_status,
            "notes": mapping.notes,
            "legal_effect": "none",
        }

    @mcp.tool()
    def validate_json(instance_path: str, schema_path: str) -> dict[str, Any]:
        """Validate a JSON file against a JSON Schema."""
        result = validate_json_schema(Path(instance_path), Path(schema_path))
        return {"ok": result.ok, "errors": list(result.errors), "legal_effect": "none"}

    @mcp.tool()
    def validate_jsonl(instance_path: str, schema_path: str) -> dict[str, Any]:
        """Validate a JSONL file against a JSON Schema."""
        result = validate_jsonl_schema(Path(instance_path), Path(schema_path))
        return {"ok": result.ok, "errors": list(result.errors), "legal_effect": "none"}

    @mcp.tool()
    def quality_gate(events_jsonl_path: str, output_path: str | None = None) -> dict[str, Any]:
        """Run event-stream certification/provenance gates."""
        result = assess_events_jsonl(Path(events_jsonl_path))
        if output_path:
            write_json(Path(output_path), result)
        result["legal_effect"] = "none"
        return result

    @mcp.resource("foio://schema/{schema_name}")
    def schema_resource(schema_name: str) -> str:
        """Return one committed JSON Schema as text."""
        path = Path("schemas/json") / schema_name
        data = loads_json(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2, sort_keys=True)

    return mcp


def run_server() -> None:
    """Run the optional MCP server."""
    server = create_server()
    server.run()
