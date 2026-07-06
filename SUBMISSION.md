# Upstream Submission: Coupling OIA Rules Module to foi-o

This directory stages a rules module for integration with `foi-o`. Upstream submission is a `[HUMAN]` task to be performed by Dylan.

## Draft PR Title
`feat: extract OIA statutory clock decisions to isolated, testable rules module`

## Draft PR Description

This pull request extracts the Official Information Act 1982 statutory deadline and clock calculations from bespoke code paths into a declarative, isolated Python module under `src/foi_o_nz/oia_rules/`. This makes statutory clock rules independently versioned and testable against explicit parameter schemas and fixture corpora.

### Motivation
By decoupling decision rules (such as response deadlines, transfer limits, extension validity, and deemed refusal) from the process pipeline and database state representation, we ensure that:
1. Changes to statutory limits or holiday periods can be expressed purely via parameterized updates without changing application control logic.
2. Compliance behavior can be fully verified in isolation using standard test fixtures.
3. Discretion points (such as urgency assessment and extension reasonableness) are cleanly isolated as routing signals requiring human verification rather than being mistakenly auto-certified.

### Staged Files
- **`src/foi_o_nz/oia_rules/__init__.py`**: Module namespace exposing types, dispatch entry points, and pure decision functions.
- **`src/foi_o_nz/oia_rules/rules.py`**: Evaluation logic implementing OIA ss 2, 12(3), 14, 15, 15A, and 28.
- **`src/foi_o_nz/oia_rules/types.py`**: Data transfer objects (`RuleInvocation`, `RuleResult`, `ValueObject`, `DiscretionPoint`) ensuring typed, isolated boundaries.
- **`src/foi_o_nz/oia_rules/parameters.json`**: PIC-conforming parameters expressing limits and calendar exclusion rules.
- **`tests/test_oia_rules.py`**: Parity tests verifying decisions, import isolation, and property round-trips.
- **`tests/fixtures/oia_rules/oia-clock-fixtures.json`**: 13 human-approved OIA clock fixtures.

### CI / Integration Notes
- Run pytest directly: `pytest tests/test_oia_rules.py`.
- Integrates with `pytest-cov` to assert >90% branch coverage on the rules module.
- Leverages the existing `foi_o_nz.dates.add_working_days` engine to preserve holiday and summer exclusion logic without double maintenance.

---
*Note: Parameters, fixtures, and trace outputs conform to the Policy Interchange Contracts (PIC) v0.1 format[^1], enabling vendor-neutral, cross-engine validation.*

[^1]: [Policy Interchange Contracts (PIC) v0.1 Specification](https://github.com/edithatogo/rulesandprocesses/tree/main/contracts)
