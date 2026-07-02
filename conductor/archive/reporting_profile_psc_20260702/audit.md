# PSC Reporting Profile Audit

Audited at: 2026-07-02T04:22:18Z

## Scope

- `src/foi_o_nz/reporting.py`
- `src/foi_o_nz/analytics.py`
- `src/foi_o_nz/table_contracts.py`
- `src/foi_o_nz/models.py`
- `mappings/psc-oia-statistics-profile.yaml`
- `schemas/json/reporting-metric.schema.json`
- `docs/08-roadmap.md`, `docs/09-backlog.md`, `docs/11-implementation-status.md`
- `README.md`

## Current State

- `foi-o-nz reporting-metrics` emits a static descriptor table from `PSC_BASE_METRICS`.
- The mapping YAML lists six PSC/OIA-related metrics with candidate event types and basic derivability labels.
- The Pydantic `ReportingMetric` model does not match the committed `reporting-metric.schema.json`: the model emits `source_profile`, while the schema requires `source_reporting_scheme` and `event_dependencies`.
- There is no committed example reporting-metric instance or aggregate PSC report output.
- There is no validator for `mappings/psc-oia-statistics-profile.yaml`.
- `analytics.py` summarises generic request/event counts but does not map events into PSC categories or classify non-derivable metrics.
- Table contracts cover requests/events/chunks/risks/review/redaction only; no aggregate reporting output contract is present.

## Gaps For Phase 1

1. Align model, schema, and mapping fields around one reporting-metric contract.
2. Require every metric to state:
   - stable metric id,
   - source reporting scheme,
   - human-readable definition,
   - derivability status,
   - event dependencies,
   - public-data limitations or exclusions,
   - official-reporting caveat.
3. Add tests that load the YAML mapping and validate all metric descriptors against the JSON Schema.
4. Cover all derivability classes needed by the roadmap: `public_fyi_derivable`, `partially_derivable`, `agency_internal_required`, and `not_derivable`.
5. Preserve the distinction between FYI-derived indicators and official PSC reporting in descriptors and CLI output.

## Deferred To Later Phases

- Aggregate report generation from event fixtures belongs to Phase 2.
- Documentation consistency checks and publication-safe README/docs updates belong to Phase 3.
- Full reporting closeout review and archive evidence belongs to Phase 4.
