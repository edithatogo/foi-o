"""Analytical table-contract export for Polars, DuckDB, Arrow, and lakehouse use."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from foi_o_nz.io import write_json

TableName = Literal["requests", "events", "chunks", "risks", "review_tasks", "redaction_candidates"]

_TABLES: dict[str, dict[str, Any]] = {
    "requests": {
        "primary_key": ["request_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("source", "utf8", False, "Source system label."),
            ("request_id", "utf8", False, "Source request identifier coerced to string."),
            ("title", "utf8", False, "Public request title."),
            ("authority", "utf8", False, "Public authority name."),
            ("source_state", "utf8", False, "Raw FYI/Alaveteli state."),
            ("normalised_state", "utf8", True, "Cautious FOI-O NZ lifecycle state."),
            ("first_sent", "timestamp[us, tz=UTC]", True, "Observed first-sent timestamp."),
            ("last_updated", "timestamp[us, tz=UTC]", True, "Observed last-updated timestamp."),
            ("content_sha256", "fixed_size_binary[32]", True, "Raw content digest when known."),
        ],
    },
    "events": {
        "primary_key": ["event_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("event_id", "utf8", False, "Event identifier."),
            ("event_type", "utf8", False, "FOI-O NZ event type."),
            ("event_time", "timestamp[us, tz=UTC]", False, "Event time."),
            ("request_id", "utf8", True, "Flattened request identifier."),
            ("lifecycle_state_after", "utf8", True, "Lifecycle state after event."),
            ("assertion_status", "utf8", False, "observed/inferred/asserted/certified/unknown."),
            ("confidence", "float64", True, "Extractor confidence."),
            ("requires_human_certification", "bool", False, "Certification-boundary flag."),
            ("machine_generated", "bool", False, "Machine-generation flag."),
        ],
    },
    "chunks": {
        "primary_key": ["chunk_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("chunk_id", "utf8", False, "Content-addressed chunk ID."),
            ("source_record_type", "utf8", False, "request or event."),
            ("source_id", "utf8", False, "Source record ID."),
            ("request_id", "utf8", True, "Request ID when known."),
            ("text", "large_utf8", False, "Chunk text."),
            ("text_sha256", "fixed_size_binary[32]", False, "Chunk text digest."),
            ("token_estimate", "int32", False, "Planning token estimate."),
        ],
    },
    "risks": {
        "primary_key": ["assessment_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("assessment_id", "utf8", False, "Risk assessment ID."),
            ("source_record_type", "utf8", False, "request/event/chunk/unknown."),
            ("source_id", "utf8", False, "Source record ID."),
            ("request_id", "utf8", True, "Request ID when known."),
            ("risk_level", "utf8", False, "low/medium/high."),
            ("review_required", "bool", False, "Human-review routing flag."),
        ],
    },
    "review_tasks": {
        "primary_key": ["task_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("task_id", "utf8", False, "Review task ID."),
            ("request_id", "utf8", True, "Request ID when known."),
            ("task_type", "utf8", False, "Review task type."),
            ("priority", "utf8", False, "low/medium/high/urgent."),
            ("source_id", "utf8", False, "Source signal ID."),
            ("decision_status", "utf8", False, "Review status."),
        ],
    },
    "redaction_candidates": {
        "primary_key": ["candidate_id"],
        "fields": [
            ("schema_version", "utf8", False, "Contract version."),
            ("candidate_id", "utf8", False, "Candidate ID."),
            ("source_id", "utf8", False, "Source record ID."),
            ("request_id", "utf8", True, "Request ID when known."),
            ("span_type", "utf8", False, "Candidate span type."),
            ("start", "int32", False, "Start offset."),
            ("end", "int32", False, "End offset."),
            ("text_sha256", "fixed_size_binary[32]", False, "Candidate text digest, not raw text."),
            ("confidence", "float64", False, "Pattern confidence."),
            ("decision_status", "utf8", False, "candidate_only_not_redacted/human_reviewed."),
        ],
    },
}


def build_table_contracts(*, include_duckdb_sql: bool = True) -> dict[str, Any]:
    """Build a table-contract manifest for downstream analytical engines."""
    tables: list[dict[str, Any]] = []
    for name, spec in sorted(_TABLES.items()):
        fields = [
            {
                "name": field_name,
                "arrow_type": arrow_type,
                "nullable": nullable,
                "description": description,
                "duckdb_type": _duckdb_type(arrow_type),
                "polars_type_hint": _polars_type(arrow_type),
            }
            for field_name, arrow_type, nullable, description in spec["fields"]
        ]
        table = {
            "name": name,
            "primary_key": spec["primary_key"],
            "fields": fields,
            "agent_boundary": "analytical_contract_only_not_source_of_legal_truth",
        }
        if include_duckdb_sql:
            table["duckdb_create_table_sql"] = _duckdb_create_sql(name, fields, spec["primary_key"])
        tables.append(table)
    return {
        "schema_version": "foi-o-nz.table-contracts.v0.1.0",
        "contract_id": "foi-o-nz-table-contracts-2026-07-01",
        "tables": tables,
        "limitations": [
            "Contracts describe derived analytical artefacts, not authoritative agency case-management data.",
            "Nested payload/evidence fields are intentionally normalised separately or retained as JSON in implementation-specific tables.",
        ],
    }


def _duckdb_type(arrow_type: str) -> str:
    if arrow_type.startswith("timestamp"):
        return "TIMESTAMPTZ"
    if arrow_type in {"utf8", "large_utf8"}:
        return "VARCHAR"
    if arrow_type == "float64":
        return "DOUBLE"
    if arrow_type == "int32":
        return "INTEGER"
    if arrow_type == "bool":
        return "BOOLEAN"
    if arrow_type.startswith("fixed_size_binary"):
        return "VARCHAR"
    return "JSON"


def _polars_type(arrow_type: str) -> str:
    if arrow_type.startswith("timestamp"):
        return "Datetime(time_zone='UTC')"
    if arrow_type in {"utf8", "large_utf8"}:
        return "String"
    if arrow_type == "float64":
        return "Float64"
    if arrow_type == "int32":
        return "Int32"
    if arrow_type == "bool":
        return "Boolean"
    if arrow_type.startswith("fixed_size_binary"):
        return "String(hex_sha256)"
    return "Object"


def _duckdb_create_sql(
    table_name: str, fields: list[dict[str, Any]], primary_key: list[str]
) -> str:
    columns = []
    for field in fields:
        nullable = "" if field["nullable"] else " NOT NULL"
        columns.append(f"  {field['name']} {field['duckdb_type']}{nullable}")
    if primary_key:
        columns.append(f"  PRIMARY KEY ({', '.join(primary_key)})")
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(columns) + "\n);"


def write_table_contracts(output: Path, *, include_duckdb_sql: bool = True) -> dict[str, Any]:
    """Write table contracts as JSON."""
    contracts = build_table_contracts(include_duckdb_sql=include_duckdb_sql)
    write_json(output, contracts)
    return {"ok": True, "output": str(output), "table_count": len(contracts["tables"])}
