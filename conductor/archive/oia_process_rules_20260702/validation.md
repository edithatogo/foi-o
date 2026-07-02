# OIA Process Rules Validation

Validated at: 2026-07-02T04:13:32Z

## Commands

| Check | Result | Notes |
| --- | --- | --- |
| `uv run pytest -q tests/test_dates.py tests/test_state_machine.py tests/test_quality.py tests/test_legal_sources.py tests/test_validation.py tests/test_schema_codegen_shacl.py` | Pass | 28 focused OIA/process-rule tests passed. |
| `uv run foi-o-nz legal-source-status` | Pass | Mapping is valid with 3 sources and 5 versioned legal references. |
| `uv run foi-o-nz legal-source-status --live --cache-dir /tmp/foi-o-nz-missing-live-cache` | Pass | Exits nonzero and reports `live_source_status: external_gate` with `live_source_unavailable`. |
| `uv run python scripts/validate_examples.py` | Pass | Example fixtures and generated reports validate. |
| `uv run foi-o-nz validate-repo` | Pass | Repository-local validation passes. |
| `uv run ruff check src tests scripts` | Pass | No lint findings. |
| `uv run ruff format --check src tests scripts` | Pass | 91 files already formatted. |
| `pixi run mojo-format-check` | Pass | Mojo formatting unchanged. |
| `pixi run mojo-test` | Pass | 25 Mojo tests passed. |

## Boundary Notes

- Holiday evidence is source-versioned through the committed Govt.nz 2026 public-holiday fixture. Regional anniversary days are explicitly excluded and surfaced as a limitation when the fixture does not include them.
- Live legal-source verification remains an external gate unless a generated cache or retriever output is supplied. The CLI fails closed in `--live` mode when no cache exists.
- Quality gates warn on unversioned or stale/unverified legal references, but they do not certify legal compliance or make dispositive OIA decisions.
