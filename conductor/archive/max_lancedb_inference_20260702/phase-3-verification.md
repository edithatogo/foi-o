# Phase 3 Verification: Bounded Extraction Experiments

Date: 2026-07-02

## Scope

- Candidate-only local/MAX extraction request packs.
- Provider provenance and deterministic fallback selection.
- Human-review routing for machine-generated candidate outputs.
- CLI request-pack generation through `prepare-local-extraction`.
- Documentation for local/MAX experiment boundaries and external gates.

## Verification Commands

- `uv run pytest -q tests/test_bounded_extraction.py tests/test_inference_providers.py tests/test_lancedb_retrieval.py tests/test_embeddings.py tests/test_retrieval_redaction_diff_pack_repro.py tests/test_agent_policy.py`
  - Result: `25 passed`.
- `uv run ruff check src tests scripts`
  - Result: passed.
- `uv run ruff format --check src tests scripts`
  - Result: `102 files already formatted`.
- `uv run python scripts/validate_examples.py`
  - Result: `examples ok`.
- `uv run foi-o-nz validate-repo`
  - Result: `repository validation ok`.
- `uv run foi-o-nz schema-drift`
  - Result: ok with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`.
- `git diff --check`
  - Result: passed.
- `uv run foi-o-nz prepare-local-extraction --input examples/request-record.jsonld --output /tmp/foi-o-local-extraction-smoke.jsonl --text-field title --provider deterministic --max-chars 80`
  - Result: one request pack written with `generated_output_included: false`, `review_required: true`, `legal_effect: none`, and `machine_certification_allowed: false`.

## Conductor Review

The `conductor-review` executable was not available in this environment. Manual review fallback checked the Phase 3 diff against the track spec. No high-confidence Phase 3 fixes remained after verification.

## Risks and External Gates

- Live MAX endpoint calls, downloaded models, GPU/accelerator tooling, and model-output quality measurement remain external gates.
- The committed surface prepares prompt packs and validates candidate-output safety only; it does not commit generated model outputs or certify legal decisions.
