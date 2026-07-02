# Final Verification: OIA process rules and legal-source versioning

Verified at: 2026-07-02T04:18:05Z

## Full Repo-Local Checks

| Command | Result |
| --- | --- |
| `uv run ruff check src tests scripts` | Pass |
| `uv run ruff format --check src tests scripts` | Pass, 91 files already formatted |
| `uv run pytest -q` | Pass, 116 tests |
| `uv run python scripts/validate_examples.py` | Pass |
| `uv run foi-o-nz validate-repo` | Pass |
| `pixi run mojo-format-check` | Pass |
| `pixi run mojo-test` | Pass, 25 Mojo tests |
| `pixi run mojo-build` | Pass |

## Closeout Decision

The track satisfies its repository-local acceptance criteria:

- Calendar tests cover weekends, public holidays, OIA summer exclusion, missing calendar data, CLI metadata preservation, and schema validation.
- Legal/guidance references include source identifiers, retrieval metadata, source status, version identifiers, and applicability basis.
- Process-rule quality gates flag missing evidence, certification-boundary violations, unversioned legal references, and stale/unverified source status.
- Live legal-source retrieval and regional anniversary calendars are bounded external gates, documented in validation and review evidence.

No further repo-local fixes are required before archiving.
