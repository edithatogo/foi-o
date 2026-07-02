# Phase 2 Verification: Dataset and Repository Publication Metadata

Scope: `publication_methods_release_20260702`, Phase 2.

## Delivered

- Added tests for dataset metadata, Croissant-style JSON-LD, Hugging Face card
  scaffolds, and repository-release metadata.
- Added repository release metadata model, schema, example fixture, writer, and
  `foi-o-nz repository-release-metadata` command.
- Strengthened publication metadata rights notices for code/docs versus source
  FYI/archive content rights.
- Aligned dataset metadata, repository-release metadata, README badge, pyproject
  URLs, and attestation build type to `https://github.com/edithatogo/foi-o`.
- Registered repository-release metadata in example and repo validators.

## Review

`conductor-review` is unavailable on `PATH` in this environment. Manual review
checked repository URL consistency, rights language, schema/example registration,
publication target labels, and avoidance of registry-publication overclaims.

## Verification

| Command | Result |
| --- | --- |
| `uv run pytest -q tests/test_publication_metadata.py tests/test_release_package.py tests/test_release_readiness_docs.py tests/test_schema_codegen_shacl.py tests/test_ledger_chunks_risk_metadata.py` | Passed, 16 tests. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 107 files already formatted. |
| `uv run python scripts/validate_examples.py` | Passed, examples ok. |
| `uv run foi-o-nz validate-repo` | Passed, repository validation ok. |
| `uv run foi-o-nz schema-drift` | Passed with known warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`. |
| `uv run foi-o-nz repository-release-metadata docs/23-release-package.md examples/release-checklist.v0.9.0.json examples/dataset-metadata.examples.json --output /tmp/foi-o-repository-release.json --release-version 0.9.0 --base-dir .` | Passed, 3 artifacts and 4 publication targets. |
| `git diff --check` | Passed. |

## Remaining gates

- Publication targets remain manual/external. This phase prepares metadata only.
- Phase 3 still needs the short methods paper and evidence checks for its claims.
