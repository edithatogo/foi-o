# OIA Rules Module Design for foi-o

This design was prepared from the local `foi-o` checkout at commit `f5527950f22a2980339472ccc4e11dbb52cf6c25`. The checkout was dirty when inspected; this package reads it as reference material only and does not modify it.

## Upstream Integration Points

- `src/foi_o_nz/dates.py` already contains `HolidayCalendar`, `add_working_days`, `is_working_day`, and `calculate_indicative_clock`. The proposed rules module should use the same calendar semantics and warning vocabulary rather than introduce a second date engine.
- `src/foi_o_nz/models.py` defines `LegalClock` as an annotation, not a legal decision. Rule outputs should remain explicit about `valueState`, warnings, and non-certifiability where a human judgment is required.
- `src/foi_o_nz/normalise.py` currently calls `calculate_indicative_clock(first_sent)` and emits a `DeadlineCalculated` `CoreEvent` with `quality_flags=["indicative_deadline_not_certified"]`. A later foi-o patch can route that event payload through the rules dispatcher when promoted fixtures exist.
- `src/foi_o_nz/cli.py` exposes `clock`, with `--decision-days`, `--transfer-days`, `--no-summer-exclusion`, and `--holidays`. The staged module should preserve this shape and add a separate deterministic rules command only after human-approved fixtures exist.
- `src/foi_o_nz/kernel_fallback.py` mirrors simple date predicates for the Mojo kernel fallback. The rules module should be pure Python first and import-isolated so a Mojo mirror can later call the same parameterized cases.
- `schemas/json/holiday-calendar.schema.json` is the source-aware holiday calendar contract. The rules module should accept the same holiday calendar object/fixture format.
- `schemas/json/core-event.schema.json` already includes `TransferAssessed`, `TransferNotified`, `DeadlineCalculated`, `ExtensionAssessed`, `ExtensionNotified`, and `OverdueFlagged`. Rule invocations should map to these event types rather than add new process vocabulary.
- Tests live under `tests/` and use pytest. New upstream tests should follow `tests/test_dates.py` style and include fixture-driven checks.

## Proposed Upstream File Map

The staged submission should propose these files under `foi-o`:

- `src/foi_o_nz/oia_rules/__init__.py`
- `src/foi_o_nz/oia_rules/rules.py`
- `src/foi_o_nz/oia_rules/types.py`
- `src/foi_o_nz/oia_rules/parameters.json`
- `tests/test_oia_rules.py`
- `tests/fixtures/oia_rules/candidates/*.json` until Dylan promotes golden fixtures.

The rules package should not import `normalise.py`, CLI code, archive readers, vector search, or process-event builders. It may import `foi_o_nz.dates` and small standard-library modules only. This keeps the import graph suitable for Python fallback use and later Mojo parity checks.

## Rule Interface

Use small dataclasses:

- `RuleInvocation`: rule id, input value objects, parameters, optional holiday calendar.
- `RuleResult`: output value objects plus trace steps.
- `DiscretionPoint`: non-computable issue requiring human certification.

Initial deterministic rule ids:

- `nz-oia/decision.response_deadline`
- `nz-oia/decision.transfer_deadline`
- `nz-oia/decision.extension_validity`
- `nz-oia/decision.deemed_refusal`
- `nz-oia/decision.urgency_flag`

Every output should carry `valueState`. Missing receipt dates must propagate as `unknown` with a warning instead of raising. Urgency and extension reasonableness must produce `DiscretionPoint` records; the module must not certify those outcomes.

## Contract Alignment

Parameters, candidate fixtures, and later traces are authored in PIC contracts:

- `pic-parameters/0.1.0` for working-day and transfer limits.
- `pic-crosswalk/0.1.0` for mapping PIC ids to foi-o model/event fields.
- `pic-fixtures/0.1.0` for candidate cases. Candidate fixtures remain `method: ai-proposed` until human curation.
- `pic-traces/0.1.0` for later runner output after promoted fixtures exist.

This package stages those artifacts under `external/foi-o/rules/` so they can be reviewed before any upstream pull request.
