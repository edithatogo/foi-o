# Conductor Review: OIA process rules and legal-source versioning

Reviewed at: 2026-07-02T04:16:25Z

## Review Mode

- `command -v conductor-review` returned no executable in this environment.
- Manual Conductor review fallback was performed against the track specification, plan, full track diff, validation evidence, and closeout/archive criteria.

## Scope Reviewed

- Source-aware holiday calendar fixture and schemas.
- Indicative clock behavior, calendar provenance, and regional-anniversary limitation warnings.
- Source-versioned legal/Ombudsman mapping and local status command.
- Fail-closed live-source gate for unavailable legal-source cache.
- Process-rule quality gates for missing evidence, unsafe certification claims, stale references, and unversioned legal references.
- Documentation and examples needed for repo-local validation.

## Findings

| Severity | Status | Finding | Resolution |
| --- | --- | --- | --- |
| Medium | Fixed | `foi-o-nz clock --holidays` loaded only holiday dates, dropping the newly introduced source metadata from the CLI output. | Fixed in `c7bbdd9`; CLI now passes the source-aware calendar object and a regression test asserts metadata/warnings. |

No remaining high-confidence fixes were identified.

## Verification After Fix

- `uv run pytest -q tests/test_dates.py tests/test_state_machine.py tests/test_quality.py tests/test_legal_sources.py tests/test_validation.py tests/test_schema_codegen_shacl.py`: 29 passed.
- `uv run python scripts/validate_examples.py`: pass.
- `uv run foi-o-nz validate-repo`: pass.
- `uv run ruff check src tests scripts`: pass.
- `uv run ruff format --check src tests scripts`: pass.

## Remaining Gates

- Live legal-source retrieval is not implemented in this track and remains an explicit external gate.
- Regional anniversary days remain excluded from the committed national holiday fixture and must be supplied separately when relevant.
- The quality gates validate evidence/provenance boundaries only; they do not certify legal correctness.
