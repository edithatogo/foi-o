# Phase 4 Validation: Inference Track Closeout

Date: 2026-07-02

## Full Repo-Local Gates

- `uv run ruff check src tests scripts`
  - Result: passed.
- `uv run ruff format --check src tests scripts`
  - Result: `102 files already formatted`.
- `uv run pytest -q`
  - Result: `147 passed`.
- `uv run python scripts/validate_examples.py`
  - Result: `examples ok`.
- `uv run foi-o-nz validate-repo`
  - Result: `repository validation ok`.
- `uv run foi-o-nz schema-drift`
  - Result: ok with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`.
- `pixi run mojo-format-check`
  - Result: passed; 20 Mojo files left unchanged.
- `pixi run mojo-test`
  - Result: passed across state, clock, text, retrieval, guardrail, transition, hash, redaction, and epistemic Mojo tests.
- `pixi run mojo-build`
  - Result: passed; built `build/foi-o-nz-mojo`.
- `git diff --check`
  - Result: passed.

## Scope Coverage

- Provider selection and provenance.
- Deterministic embeddings and provider provenance.
- LanceDB optional table/search path with deterministic fallback.
- Local/MAX candidate-only extraction request packs.
- Agent policy and certification-boundary guardrails.
- Repo examples, schemas, and Mojo fallback/native checks.

## External Gates

- Live MAX endpoint execution, downloaded model quality measurement, hosted vector services, and publication/registry checks are external gates.
- Local LanceDB is covered by fixture-backed tests in this environment.
