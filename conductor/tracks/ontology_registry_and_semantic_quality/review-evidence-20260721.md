# Review evidence — 2026-07-21

## Scope

Repository-local implementation and review of ontology registry readiness,
global namespace migration controls, and deterministic RDF quality signals.
The NZ ontology remains the compatibility/profile artifact; no global semantic
promotion or external registry submission was performed.

## Implemented

- Added `registries/ontology-namespace-migration.yaml` to record the canonical
  global namespace, NZ compatibility alias, and human approval boundary.
- Added `scripts/validate_ontology_quality.py` to validate registry status,
  readiness prerequisites, migration policy, RDF parsing, and term labels.
- Added positive and negative semantic-quality tests.
- Wired ontology validation into the Makefile and hosted programme controls.
- Generated `examples/ontology-quality-report.json` with deterministic quality
  signals.

## Validation

| Check | Result |
| --- | --- |
| `uv run python scripts/validate_ontology_quality.py` | Passed: 5 registries, 172 triples, 47 labelled terms, 0 unlabeled terms. |
| `uv run pytest -q tests/test_ontology_quality_controls.py tests/test_semantic_alignment.py` | Passed: 8 tests. |
| `uv run pytest -q` | Passed: 835 passed, 4 skipped. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed: 261 files already formatted. |
| `uv run ty check src tests scripts` | Passed. |

## Review conclusion

No unresolved repository-owned semantic-quality findings remain. Namespace
redirects, external registry submissions, ontology publication, and semantic
promotion remain human-gated.
