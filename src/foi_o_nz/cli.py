"""Command line interface for FOI-O NZ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from foi_o_nz.analytics import write_summary
from foi_o_nz.io import write_json, write_jsonl
from foi_o_nz.models import CoreEvent
from foi_o_nz.normalise import build_observed_events, build_request_profile, normalise_manifest_file
from foi_o_nz.state_machine import map_alaveteli_state
from foi_o_nz.validation import validate_json_schema, validate_rdf, validate_schema_file, validate_yaml
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


@app.command("normalise-manifest")
def normalise_manifest(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input FYI manifest JSON/JSONL")],
    requests_output: Annotated[
        Path,
        typer.Option("--requests-output", help="Output request profiles JSONL"),
    ],
    events_output: Annotated[Path, typer.Option("--events-output", help="Output events JSONL")],
    parquet_dir: Annotated[Path | None, typer.Option(help="Optional Parquet output directory")] = None,
) -> None:
    """Normalise FYI archive-style manifest records into request profiles and events."""
    manifest = normalise_manifest_file(
        input,
        requests_output=requests_output,
        events_output=events_output,
        parquet_dir=parquet_dir,
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
            "attachments": [],
            "warc_record_ids": ["warc:example:1"],
        }
    ]
    manifest_path = output_dir / "fyi-manifest.jsonl"
    write_jsonl(manifest_path, records)
    profile = build_request_profile(records[0])
    events = build_observed_events(profile)
    write_json(output_dir / "request-profile.json", profile.model_dump(mode="json", exclude_none=True))
    for event in events:
        name = str(event.event_type).replace("EventType.", "").lower().replace("_", "-")
        # Preserve predictable first filename for Makefile smoke target.
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
    example_schema_pairs = [
        (Path("examples/core-event.extension-notified.json"), Path("schemas/json/core-event.schema.json")),
        (Path("examples/agent-action.search-plan.json"), Path("schemas/json/agent-action.schema.json")),
    ]
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
