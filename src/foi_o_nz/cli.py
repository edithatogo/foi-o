"""Command line interface for FOI-O NZ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from foi_o_nz.agent_pack import write_agent_context_pack
from foi_o_nz.agent_policy import build_agent_action, evaluate_agent_action
from foi_o_nz.analytics import write_event_summary, write_summary
from foi_o_nz.batch import normalise_manifest_batch
from foi_o_nz.benchmarks import write_local_benchmarks
from foi_o_nz.chunks import chunk_jsonl
from foi_o_nz.diff import diff_jsonl
from foi_o_nz.dataset_metadata import (
    write_croissant_metadata,
    write_dataset_metadata,
    write_frictionless_datapackage,
    write_huggingface_dataset_card,
)
from foi_o_nz.ledger import build_ledger_jsonl, verify_ledger_jsonl
from foi_o_nz.redaction import propose_redactions_jsonl
from foi_o_nz.reproducibility import write_reproducibility_manifest
from foi_o_nz.retrieval import search_chunks_jsonl
from foi_o_nz.openapi import write_openapi_contract
from foi_o_nz.risk import risk_scan_jsonl
from foi_o_nz.dates import add_working_days, calculate_indicative_clock, load_holiday_dates
from foi_o_nz.duckdb_export import build_duckdb_database, write_duckdb_bootstrap_sql
from foi_o_nz.embeddings import embed_jsonl
from foi_o_nz.evaluation import evaluate_event_jsonl
from foi_o_nz.io import read_json_records, write_json, write_jsonl
from foi_o_nz.validation import load_json
from foi_o_nz.jsonld_context import write_context
from foi_o_nz.normalise import build_observed_events, build_request_profile, normalise_manifest_file
from foi_o_nz.quality import assess_events_jsonl
from foi_o_nz.rdf_export import export_rdf
from foi_o_nz.schema_codegen import compare_committed_schemas, export_generated_schemas
from foi_o_nz.shacl_validation import validate_with_shacl
from foi_o_nz.reporting import metric_table
from foi_o_nz.state_machine import RequestState, can_transition, map_alaveteli_state
from foi_o_nz.transitions import audit_transitions_jsonl
from foi_o_nz.tool_manifest import write_tool_manifest
from foi_o_nz.vector_index import build_lancedb_table
from foi_o_nz.validation import validate_json_schema, validate_jsonl_schema, validate_rdf, validate_schema_file, validate_yaml
from foi_o_nz.version import __version__

app = typer.Typer(
    name="foi-o-nz",
    help="FOI-O NZ process model, validation, and analytics workbench.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Print package version."""
    console.print(__version__)


@app.command()
def doctor() -> None:
    """Report optional dependency/tool availability."""
    import importlib.util
    import shutil

    checks = {
        "python-package": True,
        "orjson": importlib.util.find_spec("orjson") is not None,
        "msgspec": importlib.util.find_spec("msgspec") is not None,
        "polars": importlib.util.find_spec("polars") is not None,
        "duckdb": importlib.util.find_spec("duckdb") is not None,
        "lancedb": importlib.util.find_spec("lancedb") is not None,
        "rdflib": importlib.util.find_spec("rdflib") is not None,
        "pyshacl": importlib.util.find_spec("pyshacl") is not None,
        "fastmcp": importlib.util.find_spec("fastmcp") is not None,
        "mojo-cli": shutil.which("mojo") is not None,
        "max-cli": shutil.which("max") is not None,
        "pixi-cli": shutil.which("pixi") is not None,
    }
    table = Table(title="FOI-O NZ doctor")
    table.add_column("Component")
    table.add_column("Available")
    for name, ok in checks.items():
        table.add_row(name, "yes" if ok else "no")
    console.print(table)


@app.command("map-state")
def map_state(source_state: str) -> None:
    """Map an FYI/Alaveteli source state to the FOI-O NZ lifecycle vocabulary."""
    mapping = map_alaveteli_state(source_state)
    console.print_json(
        json.dumps(
            {
                "source_state": mapping.source_state,
                "normalised_state": mapping.normalised_state.value,
                "confidence": mapping.confidence,
                "assertion_status": mapping.assertion_status,
                "notes": mapping.notes,
            }
        )
    )


@app.command("can-transition")
def can_transition_command(from_state: RequestState, to_state: RequestState) -> None:
    """Check whether a lifecycle transition is permitted by the current profile."""
    ok = can_transition(from_state, to_state)
    console.print_json(
        json.dumps(
            {
                "from_state": from_state.value,
                "to_state": to_state.value,
                "allowed": ok,
            }
        )
    )
    if not ok:
        raise typer.Exit(code=2)


@app.command("clock")
def clock(
    received_date: Annotated[str, typer.Argument(help="Receipt date, YYYY-MM-DD")],
    decision_days: Annotated[int, typer.Option(help="Decision working-day interval")] = 20,
    transfer_days: Annotated[int, typer.Option(help="Transfer working-day interval")] = 10,
    no_summer_exclusion: Annotated[
        bool,
        typer.Option(help="Do not apply the OIA 25 Dec–15 Jan summer exclusion"),
    ] = False,
    holidays: Annotated[Path | None, typer.Option(help="Optional JSON/YAML holiday calendar")]=None,
) -> None:
    """Calculate an indicative OIA clock annotation."""
    from datetime import UTC, date, datetime

    parsed_date = date.fromisoformat(received_date)
    received_at = datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=UTC)
    holiday_dates = load_holiday_dates(holidays) if holidays is not None else None
    legal_clock = calculate_indicative_clock(
        received_at,
        decision_working_days=decision_days,
        transfer_working_days=transfer_days,
        holidays=holiday_dates,
        include_oia_summer_exclusion=not no_summer_exclusion,
    )
    if legal_clock is None:
        raise typer.Exit(code=1)
    console.print_json(json.dumps(legal_clock.model_dump(mode="json", exclude_none=True)))


@app.command("add-working-days")
def add_working_days_command(
    start_date: Annotated[str, typer.Argument(help="Start date, YYYY-MM-DD")],
    days: Annotated[int, typer.Argument(help="Working days to add")],
) -> None:
    """Add machine working days to a start date."""
    from datetime import date

    due = add_working_days(date.fromisoformat(start_date), days)
    console.print(due.isoformat())


@app.command("validate")
def validate(
    instance: Annotated[Path, typer.Argument(help="JSON instance file to validate")],
    schema: Annotated[Path, typer.Option(help="JSON Schema file")],
) -> None:
    """Validate a JSON file against a JSON Schema."""
    result = validate_json_schema(instance, schema)
    if not result.ok:
        for error in result.errors:
            console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]ok[/green] {instance} validates against {schema}")


@app.command("validate-jsonl")
def validate_jsonl(
    instance: Annotated[Path, typer.Argument(help="JSONL instance file to validate")],
    schema: Annotated[Path, typer.Option(help="JSON Schema file")],
) -> None:
    """Validate every line of a JSONL file against a JSON Schema."""
    result = validate_jsonl_schema(instance, schema)
    if not result.ok:
        for error in result.errors:
            console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]ok[/green] {instance} validates against {schema}")


@app.command("normalise-manifest")
def normalise_manifest(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input FYI manifest JSON/JSONL")],
    requests_output: Annotated[
        Path,
        typer.Option("--requests-output", help="Output request profiles JSONL"),
    ],
    events_output: Annotated[Path, typer.Option("--events-output", help="Output events JSONL")],
    parquet_dir: Annotated[Path | None, typer.Option(help="Optional Parquet output directory")] = None,
    run_manifest_output: Annotated[
        Path | None,
        typer.Option(help="Optional provenance run-manifest JSON output"),
    ] = None,
) -> None:
    """Normalise FYI archive-style manifest records into request profiles and events."""
    manifest = normalise_manifest_file(
        input,
        requests_output=requests_output,
        events_output=events_output,
        parquet_dir=parquet_dir,
        run_manifest_output=run_manifest_output,
    )
    console.print_json(json.dumps(manifest))


@app.command("summary")
def summary(
    requests_jsonl: Annotated[Path, typer.Argument(help="Request profile JSONL")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Summary JSON output")],
) -> None:
    """Write a lightweight JSON summary of request profiles."""
    result = write_summary(requests_jsonl, output)
    console.print_json(json.dumps(result))


@app.command("event-summary")
def event_summary(
    events_jsonl: Annotated[Path, typer.Argument(help="Core event JSONL")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Summary JSON output")],
) -> None:
    """Write a lightweight JSON summary of core events."""
    result = write_event_summary(events_jsonl, output)
    console.print_json(json.dumps(result))


@app.command("quality-gate")
def quality_gate(
    events_jsonl: Annotated[Path, typer.Argument(help="Core events JSONL")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional JSON report")]=None,
) -> None:
    """Run certification/provenance quality gates over an event stream."""
    result = assess_events_jsonl(events_jsonl)
    if output is not None:
        write_json(output, result)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-rdf")
def export_rdf_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="RDF output file")],
    requests_jsonl: Annotated[Path | None, typer.Option(help="Request profile JSONL")]=None,
    events_jsonl: Annotated[Path | None, typer.Option(help="Core events JSONL")]=None,
    fmt: Annotated[str, typer.Option("--format", help="rdflib serialisation format")]= "turtle",
) -> None:
    """Export request profiles/events to RDF."""
    result = export_rdf(
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        output=output,
        fmt=fmt,
    )
    console.print_json(json.dumps(result))


@app.command("build-duckdb")
def build_duckdb(
    database: Annotated[Path, typer.Option("--database", "-d", help="Output DuckDB database")],
    requests_jsonl: Annotated[Path | None, typer.Option(help="Request profile JSONL")]=None,
    events_jsonl: Annotated[Path | None, typer.Option(help="Core events JSONL")]=None,
    requests_parquet: Annotated[Path | None, typer.Option(help="Request Parquet file")]=None,
    events_parquet: Annotated[Path | None, typer.Option(help="Events Parquet file")]=None,
) -> None:
    """Materialise requests/events into DuckDB when the optional dependency is installed."""
    try:
        result = build_duckdb_database(
            database=database,
            requests_jsonl=requests_jsonl,
            events_jsonl=events_jsonl,
            requests_parquet=requests_parquet,
            events_parquet=events_parquet,
        )
    except RuntimeError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=1) from exc
    console.print_json(json.dumps(result))


@app.command("write-duckdb-sql")
def write_duckdb_sql(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output SQL template")],
) -> None:
    """Write a portable DuckDB SQL bootstrap file."""
    write_duckdb_bootstrap_sql(output)
    console.print(f"[green]wrote[/green] {output}")


@app.command("evaluate-events")
def evaluate_events(
    predicted: Annotated[Path, typer.Option("--predicted", help="Predicted core events JSONL")],
    gold: Annotated[Path, typer.Option("--gold", help="Gold/reference core events JSONL")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional JSON report")] = None,
    mode: Annotated[str, typer.Option(help="event_type, event_type_state, or strict")] = "event_type_state",
) -> None:
    """Evaluate candidate event extraction against a gold event set."""
    result = evaluate_event_jsonl(predicted, gold, mode=mode, output=output)  # type: ignore[arg-type]
    console.print_json(json.dumps(result))


@app.command("agent-action-template")
def agent_action_template(
    action_type: Annotated[str, typer.Argument(help="Supported agent action type")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional JSON output")] = None,
    agent_name: Annotated[str, typer.Option(help="Agent name recorded in the template")] = "foi-o-nz-agent",
) -> None:
    """Create a policy-conformant agent-action record template."""
    try:
        action = build_agent_action(action_type, agent_name=agent_name)  # type: ignore[arg-type]
    except ValueError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=1) from exc
    data = action.model_dump(mode="json", exclude_none=True)
    if output is not None:
        write_json(output, data)
    console.print_json(json.dumps(data))


@app.command("evaluate-agent-action")
def evaluate_agent_action_command(
    action_json: Annotated[Path, typer.Argument(help="Agent action JSON file")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional JSON report")] = None,
) -> None:
    """Evaluate one agent-action record against current guardrail policy."""
    result = evaluate_agent_action(load_json(action_json))
    if output is not None:
        write_json(output, result)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("normalise-batch")
def normalise_batch(
    inputs: Annotated[list[Path], typer.Argument(help="Input files, directories, or globs")],
    requests_output: Annotated[
        Path,
        typer.Option("--requests-output", help="Output request profiles JSONL"),
    ],
    events_output: Annotated[Path, typer.Option("--events-output", help="Output events JSONL")],
    parquet_dir: Annotated[Path | None, typer.Option(help="Optional Parquet output directory")] = None,
    run_manifest_output: Annotated[
        Path | None,
        typer.Option(help="Optional provenance run-manifest JSON output"),
    ] = None,
) -> None:
    """Normalise multiple FYI archive-style manifests into combined outputs."""
    result = normalise_manifest_batch(
        inputs,
        requests_output=requests_output,
        events_output=events_output,
        parquet_dir=parquet_dir,
        run_manifest_output=run_manifest_output,
    )
    console.print_json(json.dumps(result))


@app.command("transition-audit")
def transition_audit(
    events_jsonl: Annotated[Path, typer.Argument(help="Core events JSONL")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional JSON report")] = None,
) -> None:
    """Audit lifecycle transitions in an event stream."""
    result = audit_transitions_jsonl(events_jsonl)
    if output is not None:
        write_json(output, result)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=2)


@app.command("embed-jsonl")
def embed_jsonl_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Request/event JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Embedding JSONL output")],
    kind: Annotated[str, typer.Option(help="Input kind: request or event")] = "request",
    dimensions: Annotated[int, typer.Option(help="Feature-hashing vector dimensions")] = 128,
) -> None:
    """Create deterministic local embedding records for vector indexing."""
    count = embed_jsonl(input, output, kind=kind, dimensions=dimensions)
    console.print_json(json.dumps({"output": str(output), "record_count": count, "dimensions": dimensions}))


@app.command("build-lancedb")
def build_lancedb(
    embeddings_jsonl: Annotated[Path, typer.Argument(help="Embedding JSONL input")],
    database_dir: Annotated[Path, typer.Option("--database-dir", "-d", help="LanceDB directory")],
    table_name: Annotated[str, typer.Option(help="LanceDB table name")] = "foi_o_nz_embeddings",
) -> None:
    """Build an optional LanceDB vector table from embedding JSONL."""
    try:
        result = build_lancedb_table(
            embeddings_jsonl,
            database_dir=database_dir,
            table_name=table_name,
        )
    except RuntimeError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=1) from exc
    console.print_json(json.dumps(result))


@app.command("export-jsonld-context")
def export_jsonld_context(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output JSON-LD context")],
) -> None:
    """Write the FOI-O NZ JSON-LD context."""
    result = write_context(output)
    console.print_json(json.dumps(result))


@app.command("validate-shacl")
def validate_shacl(
    data_graph: Annotated[Path, typer.Argument(help="Data graph RDF file")],
    shapes_graph: Annotated[Path, typer.Option("--shapes", help="SHACL shapes graph")],
) -> None:
    """Validate RDF with SHACL when pySHACL is installed, else parse-only."""
    result = validate_with_shacl(data_graph, shapes_graph)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-schemas")
def export_schemas(
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o", help="Output directory")],
) -> None:
    """Export Pydantic-generated JSON Schemas for review/drift checks."""
    result = export_generated_schemas(output_dir)
    console.print_json(json.dumps(result))


@app.command("schema-drift")
def schema_drift(
    schema_dir: Annotated[Path, typer.Option("--schema-dir", help="Committed schema dir")] = Path("schemas/json"),
) -> None:
    """Run a shallow generated-vs-committed JSON Schema drift check."""
    result = compare_committed_schemas(schema_dir)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("mcp-server")
def mcp_server() -> None:
    """Run the optional bounded FOI-O NZ MCP server."""
    try:
        from foi_o_nz.mcp_server import run_server

        run_server()
    except RuntimeError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=1) from exc


@app.command("chunk-jsonl")
def chunk_jsonl_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Request/event JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Chunk JSONL output")],
    kind: Annotated[str, typer.Option(help="Input kind: request or event")] = "request",
) -> None:
    """Create deterministic text chunks for agent/vector workflows."""
    if kind not in {"request", "event"}:
        console.print("kind must be 'request' or 'event'", style="red")
        raise typer.Exit(code=2)
    result = chunk_jsonl(input, output, kind=kind)  # type: ignore[arg-type]
    console.print_json(json.dumps(result))


@app.command("build-ledger")
def build_ledger_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Source JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Ledger JSONL output")],
    record_type: Annotated[str, typer.Option(help="Record type label, e.g. request/event/chunk/embedding")] = "event",
    previous_hash: Annotated[str, typer.Option(help="Previous/root hash for chained ledgers")] = "0" * 64,
) -> None:
    """Create a tamper-evident SHA-256 hash-chain ledger for a JSONL stream."""
    result = build_ledger_jsonl(input, output, record_type=record_type, previous_hash=previous_hash)
    console.print_json(json.dumps(result))


@app.command("verify-ledger")
def verify_ledger_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Source JSONL input")],
    ledger: Annotated[Path, typer.Option("--ledger", "-l", help="Ledger JSONL input")],
    record_type: Annotated[str, typer.Option(help="Record type label, e.g. request/event/chunk/embedding")] = "event",
    previous_hash: Annotated[str, typer.Option(help="Previous/root hash for chained ledgers")] = "0" * 64,
) -> None:
    """Verify a tamper-evident hash-chain ledger."""
    result = verify_ledger_jsonl(input, ledger, record_type=record_type, previous_hash=previous_hash)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("risk-scan")
def risk_scan_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Request/event/chunk JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Risk assessment JSONL output")],
) -> None:
    """Run deterministic review-trigger risk triage over a JSONL stream."""
    result = risk_scan_jsonl(input, output)
    console.print_json(json.dumps(result))



@app.command("search-chunks")
def search_chunks_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Chunk JSONL input")],
    query: Annotated[str, typer.Option("--query", "-q", help="Search query")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Retrieval result JSON output")],
    top_k: Annotated[int, typer.Option(help="Number of ranked hits")] = 10,
    dimensions: Annotated[int, typer.Option(help="Feature-hashing vector dimensions")] = 128,
    lexical_weight: Annotated[float, typer.Option(help="Blend weight for lexical score, 0..1")] = 0.70,
    no_vectors: Annotated[bool, typer.Option(help="Disable local feature-hashing vector blend")] = False,
) -> None:
    """Search deterministic chunk records for agent context retrieval."""
    result = search_chunks_jsonl(
        input,
        output,
        query=query,
        top_k=top_k,
        dimensions=dimensions,
        lexical_weight=lexical_weight,
        include_vectors=not no_vectors,
    )
    console.print_json(json.dumps(result))


@app.command("propose-redactions")
def propose_redactions_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Request/event/chunk JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Candidate span JSONL output")],
    text_field: Annotated[str, typer.Option(help="Preferred text field to scan")] = "text",
) -> None:
    """Detect candidate sensitive spans without redacting or deciding."""
    result = propose_redactions_jsonl(input, output, text_field=text_field)
    console.print_json(json.dumps(result))


@app.command("diff-jsonl")
def diff_jsonl_command(
    before: Annotated[Path, typer.Option("--before", help="Earlier JSONL stream")],
    after: Annotated[Path, typer.Option("--after", help="Later JSONL stream")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Diff report JSON output")],
    key: Annotated[str | None, typer.Option(help="Optional explicit record ID field")] = None,
) -> None:
    """Diff two JSONL artefact streams by stable ID and canonical hash."""
    result = diff_jsonl(before, after, output, key=key)
    console.print_json(json.dumps(result))


@app.command("build-agent-pack")
def build_agent_pack_command(
    request_id: Annotated[str, typer.Option("--request-id", help="Request ID to package")],
    requests_jsonl: Annotated[Path, typer.Option("--requests-jsonl", help="Request profile JSONL")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Agent context pack JSON output")],
    events_jsonl: Annotated[Path | None, typer.Option("--events-jsonl", help="Core events JSONL")] = None,
    chunks_jsonl: Annotated[Path | None, typer.Option("--chunks-jsonl", help="Chunk JSONL")] = None,
    risks_jsonl: Annotated[Path | None, typer.Option("--risks-jsonl", help="Risk assessment JSONL")] = None,
    retrieval_json: Annotated[Path | None, typer.Option("--retrieval-json", help="Retrieval result JSON")] = None,
    redaction_candidates_jsonl: Annotated[
        Path | None,
        typer.Option("--redaction-candidates-jsonl", help="Redaction-candidate JSONL"),
    ] = None,
) -> None:
    """Build a request-scoped context pack for bounded agent workflows."""
    result = write_agent_context_pack(
        output,
        request_id=request_id,
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        chunks_jsonl=chunks_jsonl,
        risks_jsonl=risks_jsonl,
        retrieval_json=retrieval_json,
        redaction_candidates_jsonl=redaction_candidates_jsonl,
    )
    console.print_json(json.dumps(result))


@app.command("repro-manifest")
def repro_manifest_command(
    paths: Annotated[list[Path], typer.Argument(help="Files to digest")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Reproducibility manifest JSON output")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative file labels")] = None,
) -> None:
    """Write a reproducibility manifest for selected artefacts and local tools."""
    result = write_reproducibility_manifest(paths, output, base_dir=base_dir)
    console.print_json(json.dumps(result))


@app.command("dataset-metadata")
def dataset_metadata_command(
    paths: Annotated[list[Path], typer.Argument(help="Artifact files to describe")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Metadata JSON output")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative paths")] = None,
    frictionless: Annotated[bool, typer.Option(help="Write Frictionless-style datapackage instead")] = False,
    croissant: Annotated[bool, typer.Option(help="Write Croissant-style JSON-LD instead")] = False,
    hf_card: Annotated[bool, typer.Option(help="Write a Hugging Face dataset-card README.md instead")] = False,
) -> None:
    """Generate machine-readable publication metadata for derived artifacts."""
    selected = sum([frictionless, croissant, hf_card])
    if selected > 1:
        console.print("Choose at most one of --frictionless, --croissant, or --hf-card.", style="red")
        raise typer.Exit(code=2)
    if frictionless:
        result = write_frictionless_datapackage(paths, output, base_dir=base_dir)
    elif croissant:
        result = write_croissant_metadata(paths, output, base_dir=base_dir)
    elif hf_card:
        result = write_huggingface_dataset_card(paths, output, base_dir=base_dir)
    else:
        result = write_dataset_metadata(paths, output, base_dir=base_dir)
    console.print_json(json.dumps(result))


@app.command("export-openapi")
def export_openapi_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="OpenAPI JSON output")],
) -> None:
    """Write the bounded agent-facing OpenAPI contract skeleton."""
    result = write_openapi_contract(output)
    console.print_json(json.dumps(result))


@app.command("export-tool-manifest")
def export_tool_manifest_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Tool manifest JSON output")],
) -> None:
    """Write a bounded tool/capability manifest for agent runtimes."""
    result = write_tool_manifest(output)
    console.print_json(json.dumps(result))


@app.command("benchmark-local")
def benchmark_local_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Benchmark JSON output")],
    iterations: Annotated[int, typer.Option(help="Fixture record count")] = 1000,
) -> None:
    """Run dependency-light deterministic local microbenchmarks."""
    result = write_local_benchmarks(output, iterations=iterations)
    console.print_json(json.dumps(result))


@app.command("reporting-metrics")
def reporting_metrics() -> None:
    """Print the current PSC/OIA reporting metric descriptors."""
    console.print_json(json.dumps(metric_table()))


@app.command("smoke-fixture")
def smoke_fixture(
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o", help="Directory to write fixture files")],
) -> None:
    """Create a small valid fixture manifest, profile, and event set."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "request_id": 12345,
            "url_title": "12345_example_oia_request",
            "title": "Example OIA request",
            "authority": "Example Ministry",
            "state": "waiting_response",
            "first_sent": "2026-06-01T00:00:00Z",
            "last_updated": "2026-06-02T00:00:00Z",
            "content_sha256": "a" * 64,
            "html_captured": True,
            "attachments": [
                {"filename": "response.pdf", "url": "https://fyi.org.nz/attachment/example"},
            ],
            "warc_record_ids": ["warc:example:1"],
            "messages": [
                {
                    "id": "m1",
                    "date": "2026-06-10T00:00:00Z",
                    "body": "We need to extend the time limit for your request by 10 working days.",
                    "sender": "Example Ministry",
                }
            ],
        }
    ]
    manifest_path = output_dir / "fyi-manifest.jsonl"
    write_jsonl(manifest_path, records)
    profile = build_request_profile(records[0])
    events = build_observed_events(profile)
    write_json(output_dir / "request-profile.json", profile.model_dump(mode="json", exclude_none=True))
    for event in events:
        name = str(event.event_type).replace("EventType.", "").lower().replace("_", "-")
        if event.event_type == "RequestObserved":
            name = "request-observed"
        if event.event_type == "StateObserved":
            name = "state-observed"
        write_json(
            output_dir / f"core-event.{name}.json",
            event.model_dump(mode="json", exclude_none=True),
        )
    console.print(f"[green]wrote smoke fixture[/green] {output_dir}")


@app.command("validate-repo")
def validate_repo() -> None:
    """Validate repository schemas, examples, mappings, and RDF files."""
    errors: list[str] = []
    for schema_path in sorted(Path("schemas/json").glob("*.schema.json")):
        result = validate_schema_file(schema_path)
        errors.extend(result.errors)
    for ttl_path in [*Path("ontology").glob("*.ttl"), *Path("vocab").glob("*.ttl"), *Path("shacl").glob("*.ttl")]:
        result = validate_rdf(ttl_path)
        errors.extend(result.errors)
    for yaml_path in Path("mappings").glob("*.yaml"):
        result = validate_yaml(yaml_path)
        errors.extend(result.errors)
    for context_path in Path("contexts").glob("*.jsonld"):
        try:
            read_json_records(context_path)
        except Exception as exc:  # noqa: BLE001 - repository validation aggregation
            errors.append(f"{context_path}: invalid JSON-LD context: {exc}")
    example_schema_pairs: list[tuple[Path, Path]] = []
    example_schema_pairs.extend(
        (path, Path("schemas/json/core-event.schema.json"))
        for path in sorted(Path("examples").glob("core-event*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/agent-action.schema.json"))
        for path in sorted(Path("examples").glob("agent-action*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/request-profile.schema.json"))
        for path in sorted(Path("examples").glob("request*.jsonld"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/run-manifest.schema.json"))
        for path in sorted(Path("examples").glob("run-manifest*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/embedding-record.schema.json"))
        for path in sorted(Path("examples").glob("embedding-record*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/transition-audit.schema.json"))
        for path in sorted(Path("examples").glob("transition-audit*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/chunk-record.schema.json"))
        for path in sorted(Path("examples").glob("chunk-record*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/ledger-entry.schema.json"))
        for path in sorted(Path("examples").glob("ledger-entry*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/risk-assessment.schema.json"))
        for path in sorted(Path("examples").glob("risk-assessment*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/dataset-metadata.schema.json"))
        for path in sorted(Path("examples").glob("dataset-metadata*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/retrieval-result.schema.json"))
        for path in sorted(Path("examples").glob("retrieval-result*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/redaction-candidate.schema.json"))
        for path in sorted(Path("examples").glob("redaction-candidate*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/diff-report.schema.json"))
        for path in sorted(Path("examples").glob("diff-report*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/agent-pack.schema.json"))
        for path in sorted(Path("examples").glob("agent-pack*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/reproducibility-manifest.schema.json"))
        for path in sorted(Path("examples").glob("reproducibility-manifest*.json"))
    )
    for instance, schema in example_schema_pairs:
        if instance.exists():
            result = validate_json_schema(instance, schema)
            errors.extend(f"{instance}: {error}" for error in result.errors)
    if errors:
        for error in errors:
            console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1)
    console.print("[green]repository validation ok[/green]")


def main() -> None:
    """Entrypoint wrapper."""
    app()


if __name__ == "__main__":
    main()
