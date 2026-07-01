"""Generate JSON Schemas from Pydantic models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foi_o_nz.io import write_json
from foi_o_nz.models import AgentAction, CoreEvent, ReportingMetric, RequestProfile

SCHEMA_MODELS = {
    "agent-action.schema.json": AgentAction,
    "core-event.schema.json": CoreEvent,
    "reporting-metric.schema.json": ReportingMetric,
    "request-profile.schema.json": RequestProfile,
}


def generated_schema_map() -> dict[str, dict[str, Any]]:
    """Return generated schemas keyed by committed schema filename."""
    return {
        filename: model.model_json_schema(mode="validation")
        for filename, model in SCHEMA_MODELS.items()
    }


def export_generated_schemas(output_dir: Path) -> dict[str, Any]:
    """Write generated Pydantic JSON Schemas for review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for filename, schema in generated_schema_map().items():
        path = output_dir / filename
        write_json(path, schema)
        written.append(str(path))
    return {"output_dir": str(output_dir), "schema_count": len(written), "written": written}


def compare_committed_schemas(committed_dir: Path) -> dict[str, Any]:
    """Compare generated schemas with committed schemas by filename.

    The result is intentionally shallow: it flags missing files and top-level key
    drift. Human review remains required because hand-authored schemas may be
    stricter than Pydantic's generated form.
    """
    import json

    generated = generated_schema_map()
    findings: list[dict[str, Any]] = []
    for filename, schema in generated.items():
        path = committed_dir / filename
        if not path.exists():
            findings.append({"severity": "error", "code": "missing_schema", "file": filename})
            continue
        committed = json.loads(path.read_text(encoding="utf-8"))
        generated_keys = set(schema)
        committed_keys = set(committed)
        if generated_keys != committed_keys:
            findings.append(
                {
                    "severity": "warning",
                    "code": "top_level_schema_key_drift",
                    "file": filename,
                    "generated_only": sorted(generated_keys - committed_keys),
                    "committed_only": sorted(committed_keys - generated_keys),
                }
            )
    return {"ok": not any(item["severity"] == "error" for item in findings), "findings": findings}
