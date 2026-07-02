# Phase 2 Verification: SHACL Safety Profiles

Date: 2026-07-02

## Scope

- Required evidence/provenance constraints for process events.
- Candidate decision-like events that require human review without positive human certification.
- Unsafe agent machine-certification rejection.
- Dataset publication caveat and distribution constraints.
- pySHACL installed path and parse-only degraded mode.

## Verification Commands

- `uv run pytest -q tests/test_shacl_safety_profiles.py tests/test_semantic_alignment.py tests/test_schema_codegen_shacl.py tests/test_validation.py`
  - Result: `17 passed`.
- `uv run ruff check src tests scripts`
  - Result: passed.
- `uv run ruff format --check src tests scripts`
  - Result: `104 files already formatted`.
- `uv run python scripts/validate_examples.py`
  - Result: `examples ok`.
- `uv run foi-o-nz validate-repo`
  - Result: `repository validation ok`.
- `uv run foi-o-nz schema-drift`
  - Result: ok with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`.
- `git diff --check`
  - Result: passed.

## Conductor Review

The `conductor-review` executable was not available in this environment. Manual review fallback checked the Phase 2 diff and found no remaining high-confidence safety fixes.

## Risks and External Gates

- SHACL validates RDF profile data; JSON Schema remains the primary contract for JSON payload validation.
- pySHACL is available in the uv environment for repo-local testing. Environments without pySHACL use parse-only degraded mode and must not claim full SHACL constraint validation.
