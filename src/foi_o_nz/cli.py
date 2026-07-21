"""Command line interface for FOI-O NZ."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Annotated, Literal, cast

import typer
from rich.console import Console
from rich.table import Table

from foi_o_nz.agent_pack import write_agent_context_pack
from foi_o_nz.agent_policy import ActionType, build_agent_action, evaluate_agent_action
from foi_o_nz.analytics import write_event_summary, write_summary
from foi_o_nz.annotation import AnnotationFormat, write_annotation_tasks
from foi_o_nz.attestation import write_attestation
from foi_o_nz.batch import normalise_manifest_batch
from foi_o_nz.benchmarks import write_local_benchmarks
from foi_o_nz.bounded_extraction import write_extraction_requests
from foi_o_nz.capability_registry import build_registry_manifest, validate_registry
from foi_o_nz.cas import materialise_jsonl_cas, write_cas_manifest
from foi_o_nz.chunks import chunk_jsonl
from foi_o_nz.contract_capabilities import write_capability_declaration
from foi_o_nz.dataset_metadata import (
    write_croissant_metadata,
    write_dataset_metadata,
    write_frictionless_datapackage,
    write_huggingface_dataset_card,
    write_repository_release_metadata,
)
from foi_o_nz.dates import add_working_days, load_holiday_calendar
from foi_o_nz.diff import diff_jsonl
from foi_o_nz.duckdb_export import build_duckdb_database, write_duckdb_bootstrap_sql
from foi_o_nz.embeddings import embed_jsonl
from foi_o_nz.evaluation import MatchMode, evaluate_event_jsonl
from foi_o_nz.goldset import (
    RecordKind,
    write_goldset_sample,
    write_goldset_tasks,
    write_request_goldset_tasks,
)
from foi_o_nz.graph_export import GraphFormat, write_graph_export
from foi_o_nz.inference_providers import InferenceProviderConfig, ProviderName
from foi_o_nz.io import read_json_records, write_json, write_jsonl
from foi_o_nz.jsonld_context import write_context
from foi_o_nz.kernel_manifest import (
    write_kernel_fixtures,
    write_kernel_manifest,
    write_kernel_readiness,
)
from foi_o_nz.ledger import build_ledger_jsonl, verify_ledger_jsonl
from foi_o_nz.legal_sources import build_legal_source_status
from foi_o_nz.lineage import write_lineage_graph
from foi_o_nz.maturation import write_maturation_summary
from foi_o_nz.mcp_bundle import write_mcp_bundle
from foi_o_nz.mojo_audit import write_mojo_audit
from foi_o_nz.native_kernel import (
    evaluate_kernel,
    kernel_status,
    run_kernel_conformance,
    write_kernel_status,
)
from foi_o_nz.normalise import build_observed_events, build_request_profile, normalise_manifest_file
from foi_o_nz.oci_layout import materialise_oci_layout
from foi_o_nz.oia_rules.process import legal_clock_from_oia_rules
from foi_o_nz.openapi import write_openapi_contract
from foi_o_nz.process_advice import write_process_advice
from foi_o_nz.process_mining import (
    ProcessMiningFormat,
    write_process_mining_conformance,
    write_process_mining_export,
)
from foi_o_nz.process_models import (
    ProcessModelFormat,
    write_process_model,
    write_process_model_conformance,
)
from foi_o_nz.quality import assess_events_jsonl
from foi_o_nz.rdf_export import export_rdf
from foi_o_nz.redaction import propose_redactions_jsonl
from foi_o_nz.release_package import write_release_checklist
from foi_o_nz.replay import write_guardrail_replay
from foi_o_nz.reporting import metric_table, write_psc_aggregate_report
from foi_o_nz.reproducibility import write_reproducibility_manifest
from foi_o_nz.retrieval import search_chunks_jsonl
from foi_o_nz.review_queue import write_review_queue
from foi_o_nz.risk import risk_scan_jsonl
from foi_o_nz.schema_codegen import compare_committed_schemas, export_generated_schemas
from foi_o_nz.shacl_validation import validate_with_shacl
from foi_o_nz.state_machine import RequestState, can_transition, map_alaveteli_state
from foi_o_nz.table_contracts import write_table_contracts
from foi_o_nz.timeline import write_event_timeline
from foi_o_nz.tool_manifest import write_tool_manifest
from foi_o_nz.traces import write_trace_spans
from foi_o_nz.transitions import audit_transitions_jsonl
from foi_o_nz.validation import (
    load_json,
    validate_json_schema,
    validate_jsonl_schema,
    validate_rdf,
    validate_schema_file,
    validate_yaml,
)
from foi_o_nz.vector_index import build_lancedb_table, search_embedding_records
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


@app.command("kernel-status")
def kernel_status_command(
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional status JSON output")
    ] = None,
) -> None:
    """Report Mojo/MAX native-kernel availability and Python fallback status."""
    result = kernel_status()
    if output is not None:
        write_kernel_status(output)
    console.print_json(json.dumps(result))


@app.command("kernel-eval")
def kernel_eval_command(
    operation: Annotated[str, typer.Argument(help="Kernel operation name")],
    args: Annotated[list[str], typer.Argument(help="Operation arguments as strings")],
    no_native: Annotated[
        bool, typer.Option(help="Force Python fallback even if a Mojo binary is present")
    ] = False,
) -> None:
    """Evaluate one deterministic kernel operation with Mojo preferred and Python fallback."""
    parsed_args: list[str | int | float | bool] = []
    for value in args:
        lowered = value.lower()
        if lowered == "true":
            parsed_args.append(True)
        elif lowered == "false":
            parsed_args.append(False)
        else:
            try:
                parsed_args.append(int(value))
            except ValueError:
                try:
                    parsed_args.append(float(value))
                except ValueError:
                    parsed_args.append(value)
    try:
        result = evaluate_kernel(operation, *parsed_args, prefer_native=not no_native)
    except ValueError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=2) from exc
    console.print_json(json.dumps(result))


@app.command("kernel-conformance")
def kernel_conformance_command(
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional conformance JSON output")
    ] = None,
) -> None:
    """Run deterministic kernel conformance checks across Mojo/fallback semantics."""
    result = run_kernel_conformance(output)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("mojo-audit")
def mojo_audit_command(
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional audit JSON output")
    ] = None,
    mojo_root: Annotated[Path, typer.Option(help="Mojo source root")] = Path("mojo"),
) -> None:
    """Statically audit Mojo kernel declarations against fallback operations."""
    target = output or Path("/tmp/foi-o-nz-mojo-audit.json")
    result = write_mojo_audit(target, mojo_root=mojo_root)
    console.print_json(json.dumps(result))
    if output is None:
        with contextlib.suppress(OSError):
            target.unlink()
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-kernel-manifest")
def export_kernel_manifest_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Kernel manifest JSON output")],
    mojo_root: Annotated[Path, typer.Option(help="Mojo source root")] = Path("mojo"),
) -> None:
    """Export deterministic kernel manifest for Mojo/Python parity work."""
    result = write_kernel_manifest(output, mojo_root=mojo_root)
    console.print_json(json.dumps(result))


@app.command("export-kernel-fixtures")
def export_kernel_fixtures_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Kernel conformance JSONL output")],
) -> None:
    """Export kernel conformance fixtures for native Mojo harnesses."""
    records = write_kernel_fixtures(output)
    console.print_json(json.dumps({"ok": True, "output": str(output), "case_count": len(records)}))


@app.command("maturation-summary")
def maturation_summary_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Maturation summary JSON output")],
) -> None:
    """Export the global FOI-O ontology maturation evidence summary."""
    result = write_maturation_summary(output)
    console.print_json(json.dumps({"ok": result["ok"], "output": str(output)}))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-capabilities")
def export_capabilities_command(
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Capability declaration JSON output")
    ],
    consumer_id: Annotated[str, typer.Option(help="Declaration owner identifier")] = "foi-o-nz",
) -> None:
    """Export the versioned FOI-O consumer capability declaration."""
    result = write_capability_declaration(output, consumer_id=consumer_id)
    console.print_json(json.dumps(result))


@app.command("export-process-model")
def export_process_model_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Process model output file")],
    fmt: Annotated[
        ProcessModelFormat,
        typer.Option("--format", help="Process model format: bpmn, pnml, or mermaid"),
    ] = "bpmn",
) -> None:
    """Export canonical state-transition process models from the state machine."""
    result = write_process_model(output, fmt)
    console.print_json(json.dumps(result))


@app.command("process-model-conformance")
def process_model_conformance_command(
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Process model conformance JSON output")
    ],
) -> None:
    """Compare core BPMN/PNML process models with generated canonical exports."""
    result = write_process_model_conformance(output)
    console.print_json(json.dumps({"ok": result["ok"], "output": str(output)}))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-process-mining")
def export_process_mining_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Process-mining output file")],
    events: Annotated[
        Path,
        typer.Option("--events", help="Input JSONL or JSON event log"),
    ] = Path("examples/process-mining-events.fixture.jsonl"),
    fmt: Annotated[
        ProcessMiningFormat,
        typer.Option("--format", help="Process-mining format: xes or ocel"),
    ] = "xes",
) -> None:
    """Export fixture-only process-mining data from committed FOI-O NZ events."""
    result = write_process_mining_export(events_path=events, output=output, fmt=fmt)
    console.print_json(json.dumps(result))


@app.command("process-mining-conformance")
def process_mining_conformance_command(
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Process-mining conformance JSON output")
    ],
    events: Annotated[
        Path,
        typer.Option("--events", help="Input JSONL or JSON event log"),
    ] = Path("examples/process-mining-events.fixture.jsonl"),
) -> None:
    """Check fixture-only process-mining conformance against the release path."""
    result = write_process_mining_conformance(events, output)
    console.print_json(json.dumps({"ok": result["ok"], "output": str(output)}))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("kernel-readiness")
def kernel_readiness_command(
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional readiness JSON output")
    ] = None,
    mojo_root: Annotated[Path, typer.Option(help="Mojo source root")] = Path("mojo"),
) -> None:
    """Report what is complete and what is blocked for the Mojo-first kernel layer."""
    target = output or Path("/tmp/foi-o-nz-kernel-readiness.json")
    result = write_kernel_readiness(target, mojo_root=mojo_root)
    console.print_json(json.dumps(result))
    if output is None:
        with contextlib.suppress(OSError):
            target.unlink()


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
    holidays: Annotated[
        Path | None, typer.Option(help="Optional JSON/YAML holiday calendar")
    ] = None,
) -> None:
    """Calculate an indicative OIA clock annotation."""
    from datetime import UTC, date, datetime

    parsed_date = date.fromisoformat(received_date)
    received_at = datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=UTC)
    holiday_calendar = load_holiday_calendar(holidays) if holidays is not None else None
    # Default path dispatches through oia_rules (20/10 working days).
    # Custom intervals or disabled summer exclusion keep the dates helper.
    if decision_days == 20 and transfer_days == 10 and not no_summer_exclusion:
        legal_clock = legal_clock_from_oia_rules(
            received_at,
            holidays=holiday_calendar,
            include_oia_summer_exclusion=True,
        )
    else:
        from foi_o_nz.dates import calculate_indicative_clock

        legal_clock = calculate_indicative_clock(
            received_at,
            decision_working_days=decision_days,
            transfer_working_days=transfer_days,
            holidays=holiday_calendar,
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
    parquet_dir: Annotated[
        Path | None, typer.Option(help="Optional Parquet output directory")
    ] = None,
    run_manifest_output: Annotated[
        Path | None,
        typer.Option(help="Optional provenance run-manifest JSON output"),
    ] = None,
    live_source_url: Annotated[
        str | None,
        typer.Option(help="Optional live FYI/archive source URL recorded as an external gate"),
    ] = None,
) -> None:
    """Normalise FYI archive-style manifest records into request profiles and events."""
    manifest = normalise_manifest_file(
        input,
        requests_output=requests_output,
        events_output=events_output,
        parquet_dir=parquet_dir,
        run_manifest_output=run_manifest_output,
        live_source_url=live_source_url,
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


@app.command("build-timeline")
def build_timeline_command(
    events_jsonl: Annotated[Path, typer.Option("--events-jsonl", help="Core events JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Timeline JSON output")],
) -> None:
    """Build a deterministic event timeline with missing-date warnings."""
    result = write_event_timeline(events_jsonl, output)
    console.print_json(json.dumps(result))


@app.command("quality-gate")
def quality_gate(
    events_jsonl: Annotated[Path, typer.Argument(help="Core events JSONL")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON report")
    ] = None,
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
    requests_jsonl: Annotated[Path | None, typer.Option(help="Request profile JSONL")] = None,
    events_jsonl: Annotated[Path | None, typer.Option(help="Core events JSONL")] = None,
    fmt: Annotated[str, typer.Option("--format", help="rdflib serialisation format")] = "turtle",
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
    requests_jsonl: Annotated[Path | None, typer.Option(help="Request profile JSONL")] = None,
    events_jsonl: Annotated[Path | None, typer.Option(help="Core events JSONL")] = None,
    requests_parquet: Annotated[Path | None, typer.Option(help="Request Parquet file")] = None,
    events_parquet: Annotated[Path | None, typer.Option(help="Events Parquet file")] = None,
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
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON report")
    ] = None,
    mode: Annotated[
        str, typer.Option(help="event_type, event_type_state, or strict")
    ] = "event_type_state",
) -> None:
    """Evaluate candidate event extraction against a gold event set."""
    result = evaluate_event_jsonl(predicted, gold, mode=cast("MatchMode", mode), output=output)
    console.print_json(json.dumps(result))


@app.command("agent-action-template")
def agent_action_template(
    action_type: Annotated[str, typer.Argument(help="Supported agent action type")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON output")
    ] = None,
    agent_name: Annotated[
        str, typer.Option(help="Agent name recorded in the template")
    ] = "foi-o-nz-agent",
) -> None:
    """Create a policy-conformant agent-action record template."""
    try:
        action = build_agent_action(cast("ActionType", action_type), agent_name=agent_name)
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
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON report")
    ] = None,
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
    parquet_dir: Annotated[
        Path | None, typer.Option(help="Optional Parquet output directory")
    ] = None,
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
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON report")
    ] = None,
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
    console.print_json(
        json.dumps({"output": str(output), "record_count": count, "dimensions": dimensions})
    )


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


@app.command("search-lancedb")
def search_lancedb(
    embeddings_jsonl: Annotated[Path, typer.Argument(help="Embedding JSONL input")],
    query: Annotated[str, typer.Option("--query", "-q", help="Query text")],
    database_dir: Annotated[Path, typer.Option("--database-dir", "-d", help="LanceDB directory")],
    table_name: Annotated[str, typer.Option(help="LanceDB table name")] = "foi_o_nz_embeddings",
    top_k: Annotated[int, typer.Option("--top-k", help="Maximum result count")] = 10,
    dimensions: Annotated[int, typer.Option(help="Feature-hashing vector dimensions")] = 128,
) -> None:
    """Search optional LanceDB embeddings with deterministic fallback."""
    try:
        result = search_embedding_records(
            embeddings_jsonl,
            query_text=query,
            database_dir=database_dir,
            table_name=table_name,
            top_k=top_k,
            dimensions=dimensions,
        )
    except ValueError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=2) from exc
    console.print_json(json.dumps(result))


@app.command("prepare-local-extraction")
def prepare_local_extraction(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input JSON/JSONL records")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output request-pack JSONL")],
    text_field: Annotated[str, typer.Option(help="Input field containing source text")] = "text",
    provider: Annotated[
        str, typer.Option(help="Bounded provider selection: deterministic or max")
    ] = "deterministic",
    model: Annotated[str | None, typer.Option(help="Optional local/MAX model name")] = None,
    endpoint: Annotated[str | None, typer.Option(help="Optional local/MAX endpoint")] = None,
    max_chars: Annotated[
        int, typer.Option(help="Maximum prompt text characters per record")
    ] = 4000,
) -> None:
    """Prepare candidate-only prompt packs for local/MAX extraction experiments."""
    try:
        config = InferenceProviderConfig(
            provider=cast("ProviderName", provider), model=model, endpoint=endpoint
        )
        result = write_extraction_requests(
            input,
            output,
            text_field=text_field,
            provider_config=config,
            max_chars=max_chars,
        )
    except ValueError as exc:
        console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=2) from exc
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
    schema_dir: Annotated[Path, typer.Option("--schema-dir", help="Committed schema dir")] = Path(
        "schemas/json"
    ),
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
    result = chunk_jsonl(input, output, kind=cast("Literal['request', 'event']", kind))
    console.print_json(json.dumps(result))


@app.command("build-ledger")
def build_ledger_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Source JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Ledger JSONL output")],
    record_type: Annotated[
        str, typer.Option(help="Record type label, e.g. request/event/chunk/embedding")
    ] = "event",
    previous_hash: Annotated[str, typer.Option(help="Previous/root hash for chained ledgers")] = "0"
    * 64,
) -> None:
    """Create a tamper-evident SHA-256 hash-chain ledger for a JSONL stream."""
    result = build_ledger_jsonl(input, output, record_type=record_type, previous_hash=previous_hash)
    console.print_json(json.dumps(result))


@app.command("verify-ledger")
def verify_ledger_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Source JSONL input")],
    ledger: Annotated[Path, typer.Option("--ledger", "-l", help="Ledger JSONL input")],
    record_type: Annotated[
        str, typer.Option(help="Record type label, e.g. request/event/chunk/embedding")
    ] = "event",
    previous_hash: Annotated[str, typer.Option(help="Previous/root hash for chained ledgers")] = "0"
    * 64,
) -> None:
    """Verify a tamper-evident hash-chain ledger."""
    result = verify_ledger_jsonl(
        input, ledger, record_type=record_type, previous_hash=previous_hash
    )
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
    lexical_weight: Annotated[
        float, typer.Option(help="Blend weight for lexical score, 0..1")
    ] = 0.70,
    no_vectors: Annotated[
        bool, typer.Option(help="Disable local feature-hashing vector blend")
    ] = False,
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
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Core events JSONL")
    ] = None,
    chunks_jsonl: Annotated[Path | None, typer.Option("--chunks-jsonl", help="Chunk JSONL")] = None,
    risks_jsonl: Annotated[
        Path | None, typer.Option("--risks-jsonl", help="Risk assessment JSONL")
    ] = None,
    retrieval_json: Annotated[
        Path | None, typer.Option("--retrieval-json", help="Retrieval result JSON")
    ] = None,
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
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Reproducibility manifest JSON output")
    ],
    base_dir: Annotated[
        Path | None, typer.Option(help="Base directory for relative file labels")
    ] = None,
) -> None:
    """Write a reproducibility manifest for selected artefacts and local tools."""
    result = write_reproducibility_manifest(paths, output, base_dir=base_dir)
    console.print_json(json.dumps(result))


@app.command("build-review-queue")
def build_review_queue_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Review-task JSONL output")],
    risks_jsonl: Annotated[
        Path | None, typer.Option("--risks-jsonl", help="Risk assessment JSONL")
    ] = None,
    redaction_candidates_jsonl: Annotated[
        Path | None,
        typer.Option("--redaction-candidates-jsonl", help="Redaction-candidate JSONL"),
    ] = None,
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Core events JSONL")
    ] = None,
) -> None:
    """Build human-review tasks from candidate signals and certification boundaries."""
    result = write_review_queue(
        output,
        risks_jsonl=risks_jsonl,
        redaction_candidates_jsonl=redaction_candidates_jsonl,
        events_jsonl=events_jsonl,
    )
    console.print_json(json.dumps(result))


@app.command("process-advice")
def process_advice_command(
    request_id: Annotated[str, typer.Option("--request-id", help="Request ID to advise on")],
    requests_jsonl: Annotated[Path, typer.Option("--requests-jsonl", help="Request profile JSONL")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Process advice JSON output")],
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Core events JSONL")
    ] = None,
    review_queue_jsonl: Annotated[
        Path | None, typer.Option("--review-queue-jsonl", help="Review task JSONL")
    ] = None,
) -> None:
    """Generate non-dispositive process advice for one request."""
    result = write_process_advice(
        output,
        request_id=request_id,
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        review_queue_jsonl=review_queue_jsonl,
    )
    console.print_json(json.dumps(result))


@app.command("export-graph")
def export_graph_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Graph output file")],
    requests_jsonl: Annotated[
        Path | None, typer.Option("--requests-jsonl", help="Request profile JSONL")
    ] = None,
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Core events JSONL")
    ] = None,
    chunks_jsonl: Annotated[Path | None, typer.Option("--chunks-jsonl", help="Chunk JSONL")] = None,
    risks_jsonl: Annotated[
        Path | None, typer.Option("--risks-jsonl", help="Risk assessment JSONL")
    ] = None,
    fmt: Annotated[str, typer.Option("--format", help="json or mermaid")] = "json",
) -> None:
    """Export request/event/chunk/risk relationships as JSON or Mermaid."""
    if fmt not in {"json", "mermaid"}:
        console.print("format must be 'json' or 'mermaid'", style="red")
        raise typer.Exit(code=2)
    result = write_graph_export(
        output,
        requests_jsonl=requests_jsonl,
        events_jsonl=events_jsonl,
        chunks_jsonl=chunks_jsonl,
        risks_jsonl=risks_jsonl,
        fmt=cast("GraphFormat", fmt),
    )
    console.print_json(json.dumps(result))


@app.command("attest-artifacts")
def attest_artifacts_command(
    paths: Annotated[list[Path], typer.Argument(help="Artefact files to attest")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Attestation JSON output")],
    builder_id: Annotated[
        str, typer.Option(help="Builder ID for provenance statement")
    ] = "foi-o-nz.local",
    invocation_id: Annotated[str | None, typer.Option(help="Optional invocation ID")] = None,
) -> None:
    """Write an unsigned in-toto/SLSA-style artefact provenance statement."""
    result = write_attestation(paths, output, builder_id=builder_id, invocation_id=invocation_id)
    console.print_json(json.dumps(result))


@app.command("sample-goldset")
def sample_goldset_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input JSONL stream")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Gold-set candidate JSONL output")],
    manifest_output: Annotated[
        Path, typer.Option("--manifest-output", help="Sampling manifest JSON output")
    ],
    kind: Annotated[
        str, typer.Option(help="request, event, chunk, risk, or review_task")
    ] = "request",
    limit: Annotated[int, typer.Option(help="Maximum sampled records")] = 100,
    per_stratum: Annotated[int, typer.Option(help="Maximum records per stratum")] = 10,
    seed: Annotated[
        str, typer.Option(help="Deterministic sampling seed")
    ] = "foi-o-nz-goldset-v0.1",
) -> None:
    """Create deterministic candidate gold-set records for human labelling/evaluation."""
    if kind not in {"request", "event", "chunk", "risk", "review_task"}:
        console.print("kind must be one of request, event, chunk, risk, review_task", style="red")
        raise typer.Exit(code=2)
    result = write_goldset_sample(
        input,
        output,
        manifest_output,
        kind=cast("RecordKind", kind),
        limit=limit,
        seed=seed,
        per_stratum=per_stratum,
    )
    console.print_json(json.dumps(result))


@app.command("export-annotation-tasks")
def export_annotation_tasks_command(
    review_queue_jsonl: Annotated[
        Path, typer.Option("--review-queue-jsonl", help="Review-task JSONL")
    ],
    output: Annotated[Path, typer.Option("--output", "-o", help="Annotation output")],
    fmt: Annotated[str, typer.Option("--format", help="foio or label-studio")] = "foio",
) -> None:
    """Export neutral or Label Studio-compatible human annotation tasks."""
    if fmt not in {"foio", "label-studio"}:
        console.print("format must be 'foio' or 'label-studio'", style="red")
        raise typer.Exit(code=2)
    result = write_annotation_tasks(review_queue_jsonl, output, fmt=cast("AnnotationFormat", fmt))
    console.print_json(json.dumps(result))


@app.command("dataset-metadata")
def dataset_metadata_command(
    paths: Annotated[list[Path], typer.Argument(help="Artifact files to describe")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Metadata JSON output")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative paths")] = None,
    frictionless: Annotated[
        bool, typer.Option(help="Write Frictionless-style datapackage instead")
    ] = False,
    croissant: Annotated[bool, typer.Option(help="Write Croissant-style JSON-LD instead")] = False,
    hf_card: Annotated[
        bool, typer.Option(help="Write a Hugging Face dataset-card README.md instead")
    ] = False,
) -> None:
    """Generate machine-readable publication metadata for derived artifacts."""
    selected = sum([frictionless, croissant, hf_card])
    if selected > 1:
        console.print(
            "Choose at most one of --frictionless, --croissant, or --hf-card.", style="red"
        )
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


@app.command("release-checklist")
def release_checklist_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Release checklist JSON")],
    release_version: Annotated[
        str | None, typer.Option("--release-version", help="Release version to record")
    ] = None,
) -> None:
    """Write the machine-readable publication release checklist."""
    result = write_release_checklist(output, release_version=release_version)
    console.print_json(json.dumps(result))


@app.command("repository-release-metadata")
def repository_release_metadata_command(
    paths: Annotated[list[Path], typer.Argument(help="Release artifact files to describe")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Repository release metadata JSON")
    ],
    release_version: Annotated[str, typer.Option("--release-version", help="Release version")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative paths")] = None,
) -> None:
    """Write repository release metadata for selected artifacts."""
    result = write_repository_release_metadata(
        paths, output, base_dir=base_dir, release_version=release_version
    )
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


@app.command("validate-capability-registry")
def validate_capability_registry_command() -> None:
    """Validate the canonical profile-aware capability registry."""
    result = validate_registry()
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-capability-manifest")
def export_capability_manifest_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Capability manifest JSON output")],
) -> None:
    """Export safe tool descriptors derived from the canonical capability registry."""
    manifest = build_registry_manifest()
    write_json(output, manifest)
    console.print_json(
        json.dumps(
            {"ok": True, "output": str(output), "capability_count": len(manifest["capabilities"])}
        )
    )


@app.command("benchmark-local")
def benchmark_local_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Benchmark JSON output")],
    iterations: Annotated[int, typer.Option(help="Fixture record count")] = 1000,
) -> None:
    """Run dependency-light deterministic local microbenchmarks."""
    result = write_local_benchmarks(output, iterations=iterations)
    console.print_json(json.dumps(result))


@app.command("cas-manifest")
def cas_manifest_command(
    paths: Annotated[list[Path], typer.Argument(help="Artifact files to content-address")],
    output: Annotated[Path, typer.Option("--output", "-o", help="CAS manifest JSON output")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative paths")] = None,
) -> None:
    """Write a content-addressed manifest over selected artifacts."""
    result = write_cas_manifest(paths, output, base_dir=base_dir)
    console.print_json(json.dumps(result))


@app.command("materialise-cas")
def materialise_cas_command(
    input: Annotated[Path, typer.Option("--input", "-i", help="Source JSONL stream")],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-d", help="CAS object directory")],
    index_output: Annotated[
        Path, typer.Option("--index-output", "-o", help="CAS index JSONL output")
    ],
) -> None:
    """Materialise JSONL records as content-addressed JSON objects."""
    result = materialise_jsonl_cas(input, output_dir, index_output)
    console.print_json(json.dumps(result))


@app.command("lineage-graph")
def lineage_graph_command(
    paths: Annotated[list[Path], typer.Argument(help="Artifact files to include")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Lineage graph JSON output")],
    base_dir: Annotated[Path | None, typer.Option(help="Base directory for relative paths")] = None,
    dot_output: Annotated[
        Path | None, typer.Option("--dot-output", help="Optional Graphviz DOT output")
    ] = None,
) -> None:
    """Write a convention-derived artifact lineage graph."""
    result = write_lineage_graph(paths, output, base_dir=base_dir, dot_output=dot_output)
    console.print_json(json.dumps(result))


@app.command("trace-artifacts")
def trace_artifacts_command(
    paths: Annotated[list[Path], typer.Argument(help="Artifact files to trace")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Trace span JSONL output")],
    run_name: Annotated[str, typer.Option(help="Trace root span name")] = "foi-o-nz-local-run",
) -> None:
    """Write deterministic trace spans for local artifacts."""
    result = write_trace_spans(paths, output, run_name=run_name)
    console.print_json(json.dumps(result))


@app.command("build-goldset")
def build_goldset_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Goldset task JSONL output")],
    chunks_jsonl: Annotated[
        Path | None, typer.Option("--chunks-jsonl", help="Chunk JSONL input")
    ] = None,
    requests_jsonl: Annotated[
        Path | None,
        typer.Option("--requests-jsonl", help="Request profile JSONL input for state tasks"),
    ] = None,
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Optional core event hints JSONL")
    ] = None,
    risks_jsonl: Annotated[
        Path | None, typer.Option("--risks-jsonl", help="Optional risk assessment JSONL")
    ] = None,
    summary_output: Annotated[
        Path | None, typer.Option("--summary-output", help="Optional summary JSON output")
    ] = None,
) -> None:
    """Build bounded human annotation/evaluation tasks from request or chunk records."""
    if requests_jsonl is not None:
        result = write_request_goldset_tasks(
            requests_jsonl,
            output,
            events_jsonl=events_jsonl,
            summary_output=summary_output,
        )
    elif chunks_jsonl is not None:
        result = write_goldset_tasks(
            chunks_jsonl, output, risks_jsonl=risks_jsonl, summary_output=summary_output
        )
    else:
        console.print("Provide either --requests-jsonl or --chunks-jsonl.", style="red")
        raise typer.Exit(code=1)
    console.print_json(json.dumps(result))


@app.command("replay-guardrails")
def replay_guardrails_command(
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Guardrail replay report JSON output")
    ],
    events_jsonl: Annotated[
        Path | None, typer.Option("--events-jsonl", help="Optional core events JSONL")
    ] = None,
    actions_jsonl: Annotated[
        Path | None, typer.Option("--actions-jsonl", help="Optional agent actions JSONL")
    ] = None,
) -> None:
    """Replay certification-boundary and agent-action guardrails."""
    result = write_guardrail_replay(output, events_jsonl=events_jsonl, actions_jsonl=actions_jsonl)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("export-table-contracts")
def export_table_contracts_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Table-contract JSON output")],
    no_duckdb_sql: Annotated[
        bool, typer.Option(help="Omit DuckDB CREATE TABLE SQL snippets")
    ] = False,
) -> None:
    """Export Arrow/Polars/DuckDB-friendly analytical table contracts."""
    result = write_table_contracts(output, include_duckdb_sql=not no_duckdb_sql)
    console.print_json(json.dumps(result))


@app.command("materialise-oci")
def materialise_oci_command(
    paths: Annotated[list[Path], typer.Argument(help="Artefact files to package")],
    output_dir: Annotated[
        Path, typer.Option("--output-dir", "-o", help="Local OCI layout directory")
    ],
    base_dir: Annotated[
        Path | None, typer.Option(help="Base directory for relative labels")
    ] = None,
) -> None:
    """Materialise artefacts into a local OCI image-layout directory."""
    result = materialise_oci_layout(paths, output_dir, base_dir=base_dir)
    console.print_json(json.dumps(result))


@app.command("export-mcp-bundle")
def export_mcp_bundle_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="MCP planning bundle JSON output")],
) -> None:
    """Export a static MCP resources/prompts/tools planning bundle."""
    result = write_mcp_bundle(output)
    console.print_json(json.dumps(result))


@app.command("reporting-metrics")
def reporting_metrics() -> None:
    """Print the current PSC/OIA reporting metric descriptors."""
    console.print_json(json.dumps(metric_table()))


@app.command("psc-report")
def psc_report_command(
    events: Annotated[Path, typer.Argument(help="Event JSONL input")],
    output: Annotated[Path, typer.Option("--output", "-o", help="PSC report JSON output")],
    profile: Annotated[
        Path,
        typer.Option("--profile", help="PSC reporting profile YAML"),
    ] = Path("mappings/psc-oia-statistics-profile.yaml"),
) -> None:
    """Generate a deterministic public FYI-derived PSC-style aggregate report."""
    result = write_psc_aggregate_report(events, output, profile_path=profile)
    console.print_json(json.dumps(result))


@app.command("legal-source-status")
def legal_source_status_command(
    mapping: Annotated[
        Path,
        typer.Option("--mapping", help="Source-version mapping YAML"),
    ] = Path("mappings/nz-legislation-sources.yaml"),
    live: Annotated[
        bool,
        typer.Option(help="Check for a live-source cache; never fetch live sources directly"),
    ] = False,
    cache_dir: Annotated[
        Path,
        typer.Option(help="Ignored cache directory for externally fetched source snapshots"),
    ] = Path("generated/legal-sources"),
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional JSON status output")
    ] = None,
) -> None:
    """Validate legal-source version metadata and fail closed for live-source gates."""
    result = build_legal_source_status(mapping_path=mapping, live=live, cache_dir=cache_dir)
    if output is not None:
        write_json(output, result)
    console.print_json(json.dumps(result))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("smoke-fixture")
def smoke_fixture(
    output_dir: Annotated[
        Path, typer.Option("--output-dir", "-o", help="Directory to write fixture files")
    ],
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
    write_json(
        output_dir / "request-profile.json", profile.model_dump(mode="json", exclude_none=True)
    )
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
    for ttl_path in [
        *Path("ontology").glob("*.ttl"),
        *Path("vocab").glob("*.ttl"),
        *Path("shacl").glob("*.ttl"),
    ]:
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
        (path, Path("schemas/json/event-evaluation.schema.json"))
        for path in sorted(Path("examples").glob("event-evaluation*.json"))
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
        (path, Path("schemas/json/quality-report.schema.json"))
        for path in sorted(Path("examples").glob("quality-report*.json"))
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
    example_schema_pairs.extend(
        (path, Path("schemas/json/review-task.schema.json"))
        for path in sorted(Path("examples").glob("review-task*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/process-advice.schema.json"))
        for path in sorted(Path("examples").glob("process-advice*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/graph-export.schema.json"))
        for path in sorted(Path("examples").glob("graph-export*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/annotation-task.schema.json"))
        for path in sorted(Path("examples").glob("annotation-task*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/attestation.schema.json"))
        for path in sorted(Path("examples").glob("attestation*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/goldset-item.schema.json"))
        for path in sorted(Path("examples").glob("goldset-item*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/table-contracts.schema.json"))
        for path in sorted(Path("examples").glob("table-contracts*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/mcp-bundle.schema.json"))
        for path in sorted(Path("examples").glob("mcp-bundle*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/oci-layout-summary.schema.json"))
        for path in sorted(Path("examples").glob("oci-layout-summary*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/cas-manifest.schema.json"))
        for path in sorted(Path("examples").glob("cas-manifest*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/lineage-graph.schema.json"))
        for path in sorted(Path("examples").glob("lineage-graph*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/trace-span.schema.json"))
        for path in sorted(Path("examples").glob("trace-span*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/goldset-task.schema.json"))
        for path in sorted(Path("examples").glob("goldset-task*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/guardrail-replay.schema.json"))
        for path in sorted(Path("examples").glob("guardrail-replay*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/holiday-calendar.schema.json"))
        for path in sorted(Path("examples").glob("nz-public-holidays*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/native-kernel-status.schema.json"))
        for path in sorted(Path("examples").glob("native-kernel-status*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/kernel-conformance.schema.json"))
        for path in sorted(Path("examples").glob("kernel-conformance*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/mojo-audit.schema.json"))
        for path in sorted(Path("examples").glob("mojo-audit*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/kernel-manifest.schema.json"))
        for path in sorted(Path("examples").glob("kernel-manifest*.json"))
    )
    example_schema_pairs.extend(
        (path, Path("schemas/json/kernel-readiness.schema.json"))
        for path in sorted(Path("examples").glob("kernel-readiness*.json"))
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
