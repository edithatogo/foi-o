# Phase 4 Validation: Final Release Closeout

Scope: `publication_methods_release_20260702`, final release validation.

## Commands

| Command | Result |
| --- | --- |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 108 files already formatted. |
| `uv run pytest -q` | Passed, 166 tests. |
| `uv run python scripts/validate_examples.py` | Passed, examples ok. |
| `uv run foi-o-nz validate-repo` | Passed, repository validation ok. |
| `uv run foi-o-nz schema-drift` | Passed with known warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`. |
| `uv run foi-o-nz release-checklist --output /tmp/foi-o-release-checklist.json --release-version 0.9.0` | Passed, 6 evidence items and 5 external gates. |
| `uv run foi-o-nz repository-release-metadata docs/23-release-package.md examples/release-checklist.v0.9.0.json examples/dataset-metadata.examples.json docs/23-methods-paper.md --output /tmp/foi-o-repository-release.json --release-version 0.9.0 --base-dir .` | Passed, 4 artifacts and 4 publication targets. |
| `pixi run mojo-format-check` | Passed, 20 Mojo files unchanged. |
| `pixi run mojo-test` | Passed, all Mojo tests passed. |
| `pixi run mojo-build` | Passed, built `build/foi-o-nz-mojo`. |
| `git diff --check` | Passed. |

## External gates

- GitHub release publication requires maintainer tag/release approval.
- Hugging Face dataset publication requires credentials, terms review, and human approval.
- Zenodo or OSF deposit requires registry credentials and manual publication.
- Live FYI/archive pulls require source availability and source snapshot capture.
