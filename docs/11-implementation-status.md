# Implementation status

## Implemented in v0.1 scaffold

- Python package `foi_o_nz`.
- Pydantic models for core events, request profiles, agent actions, and reporting metrics.
- Rule-based FYI/Alaveteli state mapping.
- JSON/JSONL manifest normalisation.
- JSON Schema validation helpers.
- RDF/Turtle and YAML validation helpers.
- Optional Polars Parquet export.
- Optional DuckDB summary helper.
- Typer CLI.
- Mojo experimental deterministic state/certification kernel.
- GitHub Actions CI for Python and Mojo/MAX via Pixi.

## Not implemented yet

- Live Hugging Face dataset pull.
- MCP server.
- MAX local extraction service.
- SHACL runtime validation with pySHACL.
- Working-day calculator with official NZ holiday/closure calendars.
- LanceDB embedding index pipeline.
- Legal provision extraction from NZ Legislation API.
