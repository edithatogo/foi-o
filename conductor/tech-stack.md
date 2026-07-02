# Technology Stack

## Languages and Runtimes

- Python 3.12+ is the primary control-plane runtime.
- Mojo/MAX is the experimental compiled kernel/runtime layer.
- RDF/Turtle, JSON-LD, JSON Schema, YAML, Mermaid, and Markdown are used for semantic contracts, fixtures, mappings, diagrams, and documentation.

## Python Package and CLI

- Build backend: Hatchling.
- Package layout: `src/foi_o_nz`.
- CLI entry points: `foi-o-nz` and `foionz`, implemented with Typer and Rich.
- Core runtime libraries include Pydantic, pydantic-settings, jsonschema, PyYAML, RDFLib, Loguru, orjson, and msgspec.

## Optional Python Capabilities

- Analytics: Polars, PyArrow, DuckDB, LanceDB, and Narwhals.
- MCP: FastMCP.
- RDF validation: pySHACL.
- MAX/OpenAI experiments: OpenAI client and local/future MAX integration.
- Experiments: Instructor, Outlines, DSPy, LiteLLM, and OpenTelemetry API.

## Mojo/MAX Layer

- Mojo package lives under `mojo/foi_o_nz`.
- Mojo tests live under `mojo/tests`.
- Pixi manages Mojo/MAX environment tasks and Python editable installation.
- Mojo kernels currently cover deterministic state, clock, text, retrieval, guardrail, hash, redaction, transition, and epistemic helpers.

## Quality Tooling

- Test runner: pytest.
- Coverage: coverage.py via pytest-cov, with an 80% configured threshold.
- Lint and format: Ruff.
- Type checking: ty, currently configured with relaxed third-party import and attribute rules.
- Security and supply-chain tooling: zizmor, pip-audit, CycloneDX.
- TOML formatting/checking: taplo.
- Spelling/typos: typos.

## Common Commands

```bash
uv sync --extra dev --extra analytics --extra max --extra mcp --extra rdf --extra experiments
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run ty check
pixi install
pixi run py-quality
pixi run py-test
pixi run mojo-format-check
pixi run mojo-test
pixi run mojo-build
pixi run quality
```

## Architecture

FOI-O NZ is a standalone Python package and CLI with schema-first contracts, semantic-web artifacts, deterministic data-processing utilities, and an experimental Mojo/MAX kernel layer. The Python control plane owns mature data engineering and integration surfaces; Mojo/MAX is used for bounded deterministic kernels and future acceleration. The repository is not a monorepo and does not host the FYI archive payload.
