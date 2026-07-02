# Phase 4 Validation: Ontology Track Closeout

Date: 2026-07-02

## Full Repo-Local Gates

- `uv run ruff check src tests scripts`
  - Result: passed.
- `uv run ruff format --check src tests scripts`
  - Result: `104 files already formatted`.
- `uv run pytest -q`
  - Result: `158 passed`.
- `uv run python scripts/validate_examples.py`
  - Result: `examples ok`.
- `uv run foi-o-nz validate-repo`
  - Result: `repository validation ok`.
- `uv run foi-o-nz schema-drift`
  - Result: ok with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`.
- `pixi run mojo-format-check`
  - Result: passed; 20 Mojo files left unchanged.
- `pixi run mojo-test`
  - Result: passed across the available Mojo test set.
- `pixi run mojo-build`
  - Result: passed; built `build/foi-o-nz-mojo`.
- `git diff --check`
  - Result: passed.

## Scope Coverage

- RDF/OWL/Turtle parsing.
- SKOS vocabulary coverage.
- JSON-LD context namespace and safety/publication terms.
- pySHACL full validation path and parse-only degraded mode.
- RDF export, dataset metadata, and graph export semantic identifier consistency.

## External Gates

- Live legal-source retrieval, provision-level statutory parsing, external SHACL registry checks, and publication registry validation remain external gates.
