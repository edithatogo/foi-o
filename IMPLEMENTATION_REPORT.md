# FOI-O NZ implementation report

Generated: 2026-07-01

## Implemented

- Repo-ready standalone project structure.
- Python package `foi_o_nz` with Typer CLI.
- Pydantic models for:
  - `CoreEvent`
  - `RequestProfile`
  - `AgentAction`
  - `ReportingMetric`
- Rule-based FYI/Alaveteli state mapper.
- Manifest normalisation pipeline:
  - JSON/JSONL input
  - request-profile JSONL output
  - core-event JSONL output
  - optional Polars Parquet output
- Optional analytics helpers:
  - lightweight JSONL summaries
  - optional DuckDB Parquet summaries
- Optional MAX/OpenAI-compatible local inference client helper.
- Mojo experimental core:
  - state normalisation function
  - human-certification boundary function
  - smoke CLI
  - `TestSuite`-based tests
- CI:
  - Python lint/test/validation
  - Mojo/MAX format/test/build through Pixi
  - pip-audit/SBOM job
- Bootstrap script for creating the new GitHub repo with `gh`.

## Verified locally in this environment

```text
python -m pytest -q
14 passed

PYTHONPATH=src python -m foi_o_nz.cli map-state successful
ok

PYTHONPATH=src python -m foi_o_nz.cli smoke-fixture --output-dir /tmp/foio-smoke
ok

PYTHONPATH=src python -m foi_o_nz.cli normalise-manifest ...
ok

PYTHONPATH=src python -m foi_o_nz.cli validate /tmp/foio-smoke/core-event.request-observed.json --schema schemas/json/core-event.schema.json
ok

python -m compileall -q src tests scripts
ok
```

## Not verified locally

- Mojo compilation/tests, because the sandbox does not have the Modular Mojo toolchain installed.
- Polars/DuckDB/LanceDB extras, because they are optional and not installed in the sandbox.
- MAX serving/inference, because it requires Modular tooling and suitable local/cloud runtime.
