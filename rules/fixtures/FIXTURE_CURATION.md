# Fixture Curation Packet

Track: `oia_rules_20260704`

Promoted fixture file: `external/foi-o/rules/fixtures/oia-clock-fixtures.json`

Crosswalk file: `external/foi-o/rules/crosswalk.json`

Validation command:

```sh
contracts/tools/.venv/bin/pic-validate external/foi-o/rules
```

## Human Review Outcome

Dylan reviewed and approved all 13 candidate fixtures on 2026-07-05. The accepted fixtures have been promoted with `method: human` and `interpreterOfRecord: Dylan`.

Review basis:

- Official Information Act 1982 ss 2, 12(3), 14, 15, 15A, and 28.
- The source notes in `external/foi-o/rules/SOURCES.md`.
- The candidate public-holiday calendar assumptions for the target years.

## Candidate Coverage

- Friday receipt before a Monday public holiday.
- Transfer deadline from the same Friday-before-holiday receipt date.
- Receipt during the 25 December to 15 January exclusion.
- Receipt immediately before the 25 December to 15 January exclusion.
- Missing receipt date propagation to `unknown`.
- Extension notice after original deadline.
- Extension with large-quantity ground.
- Extension with consultation ground.
- Extension with unrecognised ground.
- Transfer deadline crossing Anzac Day Mondayisation.
- Deemed refusal after deadline.
- No deemed refusal before deadline.
- Urgency reasons as a non-computable discretion point.

## Promotion Checklist

1. [x] Confirm or correct each expected date and warning.
2. [x] Confirm whether the candidate holiday calendar assumptions are sufficient for each case.
3. [x] Move accepted cases from `rules/fixtures/candidates/` to the promoted fixture location used by the eventual upstream patch.
4. [x] Change promoted provenance from `method: ai-proposed` to `method: human`.
5. [x] Replace `interpreterOfRecord: pending Dylan review` with the actual reviewer identity.
6. [x] Record any rejected or changed candidate cases in the Phase 2 checkpoint.

No candidate cases were rejected or changed during review.
