# Phase 3 Verification: Publication-Safe Reporting Docs

Verified at: 2026-07-02T04:44:41Z

## Checks

| Command | Result | Notes |
| --- | --- | --- |
| `uv run pytest -q tests/test_reporting_docs.py tests/test_reporting.py tests/test_schema_codegen_shacl.py` | Pass | 10 docs/reporting/schema tests passed. |
| `uv run python scripts/validate_examples.py` | Pass | Reporting metric and PSC report examples validate. |
| `uv run foi-o-nz validate-repo` | Pass | Repository-local validation passed. |
| `uv run ruff check src tests scripts` | Pass | No lint findings. |
| `uv run ruff format --check src tests scripts` | Pass | 93 files already formatted. |

## Conductor Review

- `conductor-review` is unavailable in this environment, so a manual Conductor review fallback was performed against Phase 3 tests, README changes, status-page changes, and `docs/21-psc-reporting-profile.md`.
- Documentation now includes the implemented `reporting-metrics` and `psc-report` commands.
- Documentation explicitly states that FOI-O NZ reporting outputs are not official PSC reporting.
- No high-confidence Phase 3 fixes were identified after review.

## Boundary Notes

- The dedicated reporting doc explains derivability classes, sample commands, and expected `value: null` behavior for unavailable PSC metrics.
- Status documentation marks the current repo-local sample reporting surface implemented while leaving additional real-corpus reporting examples as future work.
