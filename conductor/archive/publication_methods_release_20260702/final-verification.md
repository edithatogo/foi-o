# Publication, Methods, and Release Final Verification

Scope: final closeout verification for
`publication_methods_release_20260702` after the final manual Conductor review
fallback and status-documentation fixes.

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

## Review

`conductor-review` is not available on `PATH` in this environment. The final
review used the manual Conductor review fallback and fixed stale status
statements in `README.md`, `docs/11-implementation-status.md`, and
`docs/19-release-readiness-evidence.md`.

## Completion status

Repo-local release package, repository-release metadata, release checklist, and
methods paper artefacts are complete and validated. Live registry submission,
dataset publication, source refreshes, and manual release approval remain
explicit external/manual gates.
