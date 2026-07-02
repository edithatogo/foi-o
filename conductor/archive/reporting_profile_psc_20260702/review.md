# Conductor Review: PSC reporting profile and aggregate reports

Reviewed at: 2026-07-02T04:47:41Z

## Review Mode

- `command -v conductor-review` returned no executable in this environment.
- Manual Conductor review fallback was performed against the track specification, plan, full track diff, phase verification evidence, validation evidence, examples, schemas, and CLI outputs.

## Scope Reviewed

- PSC reporting metric mapping and derivability classifications.
- Reporting metric schema and sample metric descriptor.
- PSC aggregate report builder, CLI command, schema, committed fixture, and sample report.
- Publication-safe README/status/docs language and documentation checks.
- Closeout validation evidence and archive readiness.

## Findings

| Severity | Status | Finding | Resolution |
| --- | --- | --- | --- |
| Medium | Fixed | Phase 1 source/category review found the profile should use the specific PSC OIA statistics source page and include the average-time-to-respond category. | Fixed in `a0b7c8d`. |
| Medium | Fixed | Phase 2 review found timeliness and average-time-to-respond were returning contextual counts in `value`, which could imply official metric calculation. | Fixed in `11e3cbc`; these metrics now keep `value: null` and use `public_indicator_count` only. |

No remaining high-confidence fixes were identified.

## Verification Basis

- `validation.md` records focused reporting/docs/analytics/schema/table tests, example validation, repo validation, Ruff check/format, and reporting CLI checks.
- Phase evidence files record manual review fallback after each implementation phase.

## Remaining Gates

- Real-corpus PSC report examples remain future work.
- Official PSC reporting, agency-internal records, Ombudsman complaint status, and authoritative timeliness calculations remain outside the public FYI-derived repo-local evidence boundary.
