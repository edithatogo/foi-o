"""Command line interface for FOI-O NZ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from foi_o_nz.analytics import write_event_summary, write_summary
from foi_o_nz.dates import add_working_days, calculate_indicative_clock, load_holiday_dates
from foi_o_nz.duckdb_export import build_duckdb_database, write_duckdb_bootstrap_sql
from foi_o_nz.io import write_json, write_jsonl
from foi_o_nz.normalise import build_observed_events, build_request_profile, normalise_manifest_file
from foi_o_nz.quality import assess_events_jsonl
from foi_o_nz.rdf_export import export_rdf
from foi_o_nz.reporting import metric_table
from foi_o_nz.state_machine import RequestState, can_transition, map_alaveteli_state
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
        "polars": importlib.util.find_spec("polars") is not None,
        "duckdb": importlib.util.find_spec("duckdb") is not None,
        "lancedb": importlib.util.find_spec("lancedb") is not None,
        "rdflib": importlib.util.find_spec("rdflib") is not None,
        "pyshacl": importlib.util.find_spec("pyshacl") is not None,
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
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print_json(json.dumps(result))


@app.command("write-duckdb-sql")
def write_duckdb_sql(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output SQL template")],
) -> None:
    """Write a portable DuckDB SQL bootstrap file."""
    write_duckdb_bootstrap_sql(output)
    console.print(f"[green]wrote[/green] {output}")


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
