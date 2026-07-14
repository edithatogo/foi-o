# Import and validation audit

- Target repository: `https://github.com/edithatogo/foi-o.git`
- Starting branch: `main`
- Starting SHA: `360f48b1806ad48f0c84d07ba6528402cdaeedfe`
- Archive: `foi-o-v2-codex-one-shot.zip`
- Archive SHA-256: `54fe940d77f283fb933e345bc6ad2daf2d85914b8c10eba2a3c882c85be64e13`
- Archive safety: no absolute paths, traversal entries, or symlinks detected.
- Bootstrap report: local-only `.codex/foi-o-v2-bootstrap-report.json`
- Bootstrap outcome: 87 created files, 0 identical, 0 conflicts, 0 manual entries.

The system Python command failed because `jsonschema` was unavailable. Bundle
validation then ran through declared environments. The bundle's editable build
also failed because setuptools discovered multiple flat top-level packages; the
reviewed archive was not modified. Its declared dependencies were instead used
in an isolated non-installing `uv` environment for work-package tests.

No captured page or attachment content was executed. No sibling repository was
modified because sibling discovery is intentionally inactive for a `foi-o` target.

## Integration result

- Implementation commit: `a966b3a`
- ADR namespace: reconciled to `0006` through `0010`.
- Documentation namespace: reconciled to `33` through `40`.
- Existing package/runtime boundary: `foi-o-nz`, `foi_o_nz`, native state mapping,
  and native `oia_rules` retained.
- Bootstrap conflicts: none; native numbering and registration decisions were
  still applied after bootstrap.

## Validation outcomes

- `uv run --project ... python tools/validate_bundle.py`: passed; 213 checksums.
- Bundle tests: 8 passed.
- Isolated staged packages: FOI-O 7, fyi-archive 2, nlp-policy-nz 3 passed.
- `uv run pytest -q tests/test_empirical_contracts.py tests/test_empirical_schema_fixtures.py`: 57 passed.
- `uv run pytest -q`: 274 passed.
- `uv run ruff check src tests scripts`: passed.
- `uv run ruff format --check src tests scripts`: passed.
- `uv run python scripts/validate_examples.py`: passed.
- `uv run foi-o-nz validate-repo`: passed.
- `pixi run py-quality`: passed.
- `uv build`: source distribution and wheel passed; wheel contains
  `foi_o_nz/empirical_contracts.py`.
- `uv run ty check` on new empirical files: passed.
- Full `uv run ty check`: 111 pre-existing diagnostics outside the overlay.
- Coverage run: 274 tests passed; `empirical_contracts.py` reached 91%, while
  repository-wide coverage remained 78.75% against the existing 80% threshold.
- `conductor-review`: unavailable in repository tooling.
- Stale staged command `foi-o-nz validate-all`: unavailable; replaced by the
  repository-native `foi-o-nz validate-repo`, which passed.

No validation failure was concealed. The full-type and repository-wide coverage
gaps remain explicit baseline gates rather than being attributed to the overlay.
