# Reporting Validation

Validated at: 2026-07-02T04:46:25Z

## Commands

| Check | Result | Notes |
| --- | --- | --- |
| `uv run pytest -q tests/test_reporting.py tests/test_reporting_docs.py tests/test_analytics.py tests/test_table_oci_mcp_bundle.py tests/test_schema_codegen_shacl.py tests/test_validation.py` | Pass | 18 focused reporting/analytics/schema/table tests passed. |
| `uv run python scripts/validate_examples.py` | Pass | Reporting metric and PSC report examples validate. |
| `uv run foi-o-nz validate-repo` | Pass | Repository-local validation passed. |
| `uv run ruff check src tests scripts` | Pass | No lint findings. |
| `uv run ruff format --check src tests scripts` | Pass | 93 files already formatted. |
| `uv run foi-o-nz psc-report examples/events.psc-report-sample.jsonl --output /tmp/foi-o-nz-psc-report-closeout.json` | Pass | CLI generated deterministic sample report. |
| `uv run foi-o-nz reporting-metrics` | Pass | Output includes `psc.average_time_to_respond` and non-official PSC reporting caveats. |

## Boundary Notes

- Aggregate reports are public FYI-derived indicators only and are not official PSC reporting.
- Metrics that cannot be calculated from public events keep `value: null` and expose contextual `public_indicator_count` where useful.
- Agency-internal-required and not-derivable metrics are explicitly flagged in both descriptors and reports.
