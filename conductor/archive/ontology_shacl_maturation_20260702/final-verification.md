# Ontology and SHACL final verification

Scope: final closeout verification for `ontology_shacl_maturation_20260702`
after the manual Conductor review fallback and status-documentation fixes.

## Commands

| Command | Result |
| --- | --- |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 104 files already formatted. |
| `uv run pytest -q` | Passed, 158 tests. |
| `uv run python scripts/validate_examples.py` | Passed, examples ok. |
| `uv run foi-o-nz validate-repo` | Passed, repository validation ok. |
| `uv run foi-o-nz schema-drift` | Passed with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`. |
| `pixi run mojo-format-check` | Passed, 20 Mojo files unchanged. |
| `pixi run mojo-test` | Passed, all Mojo tests passed. |
| `pixi run mojo-build` | Passed, built `build/foi-o-nz-mojo`. |
| `git diff --check` | Passed. |

## Review

`conductor-review` is not available on `PATH` in this environment. The final
review used the manual Conductor review fallback and fixed stale status
statements in `README.md`, `docs/11-implementation-status.md`, and
`conductor/tracks.md`.

## Boundaries

- pySHACL is covered through the installed runtime path and the documented
  parse-only degraded mode.
- Live legal-source retrieval, external SHACL registry checks, and publication
  registry validation remain external gates.
