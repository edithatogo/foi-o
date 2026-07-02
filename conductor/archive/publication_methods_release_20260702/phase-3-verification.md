# Phase 3 Verification: Methods Paper

Scope: `publication_methods_release_20260702`, Phase 3.

## Delivered

- Added `tests/test_methods_paper.py` to check required paper sections,
  repo-local evidence citations, validation commands, and overclaiming guards.
- Added `docs/23-methods-paper.md`, a concise methods paper covering
  motivation, architecture, data model, human-certification boundary,
  evaluation, limitations, and reproducibility.
- Updated the release checklist fixture and repository-release metadata fixture
  so the methods paper is a repo-local publication artifact.
- Updated `docs/23-release-package.md` with the methods paper in the
  repository-release metadata regeneration command.

## Review

`conductor-review` is unavailable on `PATH` in this environment. Manual review
checked required evidence references, reproducibility commands, boundary
phrases, forbidden overclaiming phrases, and updated publication metadata.

## Verification

| Command | Result |
| --- | --- |
| `uv run pytest -q tests/test_methods_paper.py tests/test_publication_metadata.py tests/test_release_package.py tests/test_release_readiness_docs.py tests/test_schema_codegen_shacl.py` | Passed, 13 tests. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 108 files already formatted. |
| `uv run python scripts/validate_examples.py` | Passed, examples ok. |
| `uv run foi-o-nz validate-repo` | Passed, repository validation ok. |
| `uv run foi-o-nz schema-drift` | Passed with known warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`. |
| `uv run foi-o-nz repository-release-metadata docs/23-release-package.md examples/release-checklist.v0.9.0.json examples/dataset-metadata.examples.json docs/23-methods-paper.md --output /tmp/foi-o-repository-release.json --release-version 0.9.0 --base-dir .` | Passed, 4 artifacts and 4 publication targets. |
| `uv run foi-o-nz release-checklist --output /tmp/foi-o-release-checklist.json --release-version 0.9.0` | Passed, 6 evidence items and 5 external gates. |
| `git diff --check` | Passed. |

## Remaining gates

- The methods paper is a local draft prepared for manual publication review.
- Registry submission and release publication remain explicit external/manual
  gates.
