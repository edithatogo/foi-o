# Specification: OIA process rules and legal-source versioning

## Objective

Add official NZ holiday/closure calendar support, source-versioned OIA/Ombudsman references, and stronger process-rule quality gates.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/14
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Support a documented working-day calendar model for NZ public holidays and OIA summer closure periods.
- Keep clock calculations indicative, provenance-bearing, and non-certifying.
- Add source-version metadata for legislation, Ombudsman guidance, and process-rule references.
- Strengthen quality gates for missing evidence, stale source references, and unsafe certification claims.

## Acceptance Criteria

- Calendar tests cover weekends, public holidays, summer exclusion, missing source data, and boundary dates.
- Legal/guidance references include stable identifiers, retrieval metadata, and version notes.
- Process-rule quality gates fail closed on missing or uncertified decision-like claims.
- Live NZ Legislation/Ombudsman access is recorded as an external gate when unavailable.
