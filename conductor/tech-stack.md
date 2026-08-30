# Technology Stack

## Languages and Runtimes

- Python 3.14 is the only supported control-plane runtime (`requires-python = ">=3.14"`; CI tests 3.14.5).
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

- Test runner: pytest with pytest-xdist for the normal four-worker local/CI
  profile and a retained serial scheduled/release profile.
- Coverage: coverage.py via pytest-cov, with an 80% configured threshold.
- Lint and format: Ruff.
- Type checking: ty for rapid feedback and BasedPyright with the tracked
  no-regression baseline plus a staged strict-mode ratchet over repaired runtime
  modules for the final static gate. Narrow exclusions preserve
  authorization-pinned executable governance files. Static analysis complements
  rather than replaces behavioral tests.
- Security and supply-chain tooling: zizmor, pip-audit, CycloneDX.
- Dependency robustness: Renovate lockfile maintenance (weekly, AI SDKs grouped);
  scheduled dependency-head (`uv lock --upgrade`) and dependency-floor
  (`uv lock --resolution lowest-direct`) fast-suite jobs in
  `.github/workflows/dependency-validation.yml`; pixi/uv environment parity gate
  (`make env-parity`, `scripts/check_env_parity.py`); monotonic coverage
  ratchet (`make coverage-ratchet`, baseline in `.coverage-baseline.json`).
- Adapter-boundary policy: AI SDKs (`openai`, `litellm`, `instructor`, `fastmcp`)
  may only be imported inside their designated adapter modules, enforced by the
  ruff `TID251` banned-api rule. Upstream SDK major-version churn stays
  isolated to a single file.

## Source Archive Migration

- `edithatogo/fyi-archive` has been archived as the historical capture and
  orchestration project. Its active functionality is succeeded by
  `edithatogo/fyi-cli` (Rust workspace: `fyi-cli`, `fyi-core`, `fyi-mcp`),
  which performs multi-jurisdiction FOI capture against Alaveteli platforms.
- Historical evidence, manifests, and provenance records that reference
  `edithatogo/fyi-archive` remain valid as historical records and must not be
  rewritten. New cross-repo dependencies and coordination entries point to
  `edithatogo/fyi-cli`.
- The published dataset `edithatogo/fyi-archive-nz` on Hugging Face is
  unaffected by the repository migration and remains the governed NZ corpus
  source for empirical work.
- TOML formatting/checking: taplo.
- Spelling/typos: typos.

## Common Commands

```bash
uv sync --extra dev --extra analytics --extra max --extra mcp --extra rdf --extra experiments
make test-fast
make test-full
make test-serial
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
