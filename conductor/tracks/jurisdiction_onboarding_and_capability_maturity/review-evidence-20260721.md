# Review evidence — 2026-07-21

## Scope

Repository-local implementation and review of jurisdiction profile lifecycle,
capability maturity, source-pack readiness, and access-policy controls. No
profile was promoted and no live capture or legal interpretation was performed.

## Implemented

- Added `scripts/validate_jurisdiction_profiles.py` to cross-check the profile
  registry, maturity dimensions, jurisdiction-pack template, and access policy.
- Added positive and negative tests for missing maturity entries and incomplete
  live-capture prohibitions.
- Wired the validator into the Makefile and hosted programme-control workflow.
- Regenerated the ontology maturation summary and corrected its coverage-matrix
  test-module count after repository inventory drift was detected.

## Validation

| Check | Result |
| --- | --- |
| `uv run pytest -q` | Passed: 832 passed, 4 skipped. |
| `uv run pytest -q tests/test_jurisdiction_registry_controls.py tests/test_jurisdiction_profiles.py` | Passed: 7 tests. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed: 259 files already formatted. |
| `uv run ty check src tests scripts` | Passed. |
| `uv run basedpyright` | Passed. |
| `uv run python tests/validate_repo.py` | Passed. |
| `uv run python scripts/validate_requirements.py` | Passed: 11 requirements, no errors. |
| `uv run python scripts/validate_jurisdiction_profiles.py` | Passed: 3 profiles, no errors. |
| `uv run python scripts/validate_workflows.py` | Passed. |
| `uv run python scripts/version_tool.py check` | Passed. |
| `uv run python -m foi_o_nz.cli validate-capability-registry` | Passed. |
| `actionlint .github/workflows/*.yml` | Passed. |
| `uv run zizmor --min-severity medium .github/workflows` | Passed: no findings, 2 suppressed. |

## Review conclusion

No unresolved repository-owned implementation or validation findings remain for
this tranche. Source rights, operator access, immutable capture, independent
annotation, legal review, and profile promotion remain explicit human gates.
