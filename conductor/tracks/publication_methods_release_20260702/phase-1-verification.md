# Phase 1 Verification: Release Evidence Package

Scope: `publication_methods_release_20260702`, Phase 1.

## Delivered

- Audited existing release-readiness evidence, metadata generators,
  reproducibility manifests, and publication gaps.
- Added release checklist tests covering schema/example validation, required
  commands, existing evidence paths, external-gate labels, rights notices, and
  missing-evidence errors.
- Added `src/foi_o_nz/release_package.py` with a Pydantic release checklist
  model, validator, and writer.
- Added `schemas/json/release-checklist.schema.json` and
  `examples/release-checklist.v0.9.0.json`.
- Added `foi-o-nz release-checklist`.
- Added `docs/23-release-package.md` and linked checklist validation from
  `docs/19-release-readiness-evidence.md`.
- Review fix: aligned stale repository URLs to `https://github.com/edithatogo/foi-o`.

## Review

`conductor-review` is unavailable on `PATH` in this environment. Manual
Conductor review checked release checklist paths, external-gate wording, rights
boundaries, docs, schema registration, and repository URL consistency.

## Verification

| Command | Result |
| --- | --- |
| `uv run pytest -q tests/test_release_package.py tests/test_release_readiness_docs.py tests/test_schema_codegen_shacl.py tests/test_ledger_chunks_risk_metadata.py tests/test_review_advice_graph_attestation_gold_annotation.py` | Passed, 21 tests. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 106 files already formatted. |
| `uv run python scripts/validate_examples.py` | Passed, examples ok. |
| `uv run foi-o-nz validate-repo` | Passed, repository validation ok. |
| `uv run foi-o-nz schema-drift` | Passed with known warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`. |
| `uv run foi-o-nz release-checklist --output /tmp/foi-o-release-checklist.json --release-version 0.9.0` | Passed, 6 evidence items and 5 external gates. |
| `git diff --check` | Passed. |

## Remaining gates

- GitHub release publication, Hugging Face dataset publication, Zenodo/OSF
  deposit, live FYI/archive pulls, and native Mojo/MAX release certification
  remain explicit external/manual gates.
- Phase 2 still needs richer dataset/repository publication metadata updates.
