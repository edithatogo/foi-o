# Final Verification: PSC reporting profile and aggregate reports

Verified at: 2026-07-02T04:49:10Z

## Full Repo-Local Checks

| Command | Result |
| --- | --- |
| `uv run ruff check src tests scripts` | Pass |
| `uv run ruff format --check src tests scripts` | Pass, 93 files already formatted |
| `uv run pytest -q` | Pass, 123 tests |
| `uv run python scripts/validate_examples.py` | Pass |
| `uv run foi-o-nz validate-repo` | Pass |
| `pixi run mojo-format-check` | Pass |
| `pixi run mojo-test` | Pass, 25 Mojo tests |
| `pixi run mojo-build` | Pass |

## Closeout Decision

The track satisfies its repository-local acceptance criteria:

- Reporting mappings are schema validated and include derivability, public-data limitations, exclusions, and non-official PSC reporting caveats.
- Sample aggregate reports are generated from a committed fixture and validate against `schemas/json/psc-report.schema.json`.
- Tests cover public-FYI derivable, partially derivable, agency-internal-required, and not-derivable metrics.
- Documentation separates public FYI-derived indicators from official PSC reporting.

No further repo-local fixes are required before archiving.
