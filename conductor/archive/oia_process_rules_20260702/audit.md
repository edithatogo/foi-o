# OIA process rules calendar and source audit

Date: 2026-07-02

Scope: Phase 1 audit of clock helpers, Mojo kernels, mappings, examples, and
documentation before calendar-contract tests.

## Current Clock Surface

- `src/foi_o_nz/dates.py` provides deterministic dependency-light helpers for:
  - ISO-ish datetime parsing.
  - Weekend exclusion.
  - OIA summer exclusion from 25 December through 15 January inclusive.
  - Optional JSON/YAML holiday-file loading.
  - Indicative decision and transfer due dates.
- `foi-o-nz clock` accepts `--holidays` and `--no-summer-exclusion`.
- Clock output is intentionally non-certifying through `LegalClock.warnings`.
- Missing holiday data is currently represented by
  `public_holidays_not_supplied`.

## Current Test Coverage

- `tests/test_dates.py` covers:
  - `Z` suffix parsing.
  - Weekend skip behavior.
  - Summer-exclusion boundary dates.
  - Basic clock creation.
  - Basic JSON holiday date loading.
- Missing coverage:
  - Public-holiday effect on actual due dates.
  - Calendar metadata/provenance.
  - Missing/empty official calendar behavior.
  - CLI `clock --holidays` output contract.
  - Holiday data structures with source/retrieval metadata.

## Mojo Clock Surface

- `mojo/foi_o_nz/clock.mojo` covers:
  - Weekend predicate.
  - OIA summer-exclusion predicate.
  - Simple machine-working-day predicate.
- It does not currently accept public-holiday data or calculate due dates.
- `mojo/tests/test_clock.mojo` mirrors only summer and weekend behavior.

## Legal and Guidance References

- `LegalReference` already supports `uri`, `work_id`, `version_id`,
  `retrieved_at`, and `applicability_basis`.
- `docs/06-legal-versioning.md` describes the desired minimum legal-reference
  model.
- `mappings/nz-legislation-sources.yaml` has source ids, work ids, canonical
  URIs, and initial OIA references.
- Missing source-versioning pieces:
  - `retrieved_at`, `version_id`, and source status are absent from mapping
    records.
  - Ombudsman guidance is not represented as a versioned source.
  - Extractor-created legal references remain mostly bare source/reference
    dictionaries without version metadata.

## Calendar Assumptions to Harden

- Public holidays are caller-supplied, not bundled.
- Regional anniversary days are warned about but not modeled.
- OIA summer exclusion is hard-coded as 25 December through 15 January.
- Calculations are indicative and should keep warning strings explicit.
- Live NZ Legislation/Ombudsman/calendar retrieval remains an external gate
  unless a fail-closed cache/download command is added.
