# Phase 1 Verification: Reporting Mapping Baseline

Verified at: 2026-07-02T04:30:10Z

## Checks

| Command | Result | Notes |
| --- | --- | --- |
| `uv run pytest -q tests/test_reporting.py tests/test_analytics.py tests/test_table_oci_mcp_bundle.py tests/test_schema_codegen_shacl.py` | Pass | 10 focused reporting/schema/table tests passed. |
| `uv run python scripts/validate_examples.py` | Pass | Includes `reporting-metric*.json`. |
| `uv run foi-o-nz validate-repo` | Pass | Repository-local validation passed. |
| `uv run ruff check src tests scripts` | Pass | No lint findings. |
| `uv run ruff format --check src tests scripts` | Pass | 92 files already formatted. |
| `uv run foi-o-nz reporting-metrics` | Pass | Output includes `psc.average_time_to_respond` and the non-official PSC reporting caveat. |

## Conductor Review

- `conductor-review` is unavailable in this environment, so a manual Conductor review fallback was performed against the Phase 1 plan, track spec, mapping contract, tests, examples, and descriptor CLI output.
- One high-confidence source/category fix was applied in `a0b7c8d`: the profile now points to the specific PSC OIA statistics page and includes `psc.average_time_to_respond`.
- No remaining high-confidence Phase 1 fixes were identified.

## Boundary Notes

- The mapping describes public FYI-derived research indicators and explicitly states they are not official PSC reporting.
- Metrics that require agency-internal records or Ombudsman/agency reporting are marked `agency_internal_required` or `not_derivable`.
- Aggregate report generation is not part of Phase 1 and remains Phase 2 work.
