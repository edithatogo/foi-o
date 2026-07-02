# Phase 1 Verification: Provider Interface

Date: 2026-07-02

## Scope

Phase 1 introduced a bounded provider-selection contract for deterministic and
MAX/OpenAI-compatible embedding experiments, plus provider provenance in
embedding records.

Changed implementation surfaces:

- `src/foi_o_nz/inference_providers.py`
- `src/foi_o_nz/embeddings.py`
- `tests/test_inference_providers.py`
- `schemas/json/embedding-record.schema.json`
- `examples/embedding-record.request.json`
- `conductor/tracks/max_lancedb_inference_20260702/audit.md`

## Automated Verification

Passed:

```bash
uv run pytest -q tests/test_inference_providers.py tests/test_embeddings.py tests/test_retrieval_redaction_diff_pack_repro.py tests/test_agent_policy.py
```

Result: `17 passed`.

Passed:

```bash
tmpdir=$(mktemp -d)
printf '%s\n' '{"request_id":"1","title":"Health data","authority":"Agency","source_state":"waiting_response","normalised_state":"Received"}' > "$tmpdir/requests.jsonl"
uv run foi-o-nz embed-jsonl --input "$tmpdir/requests.jsonl" --output "$tmpdir/embeddings.jsonl" --kind request --dimensions 8
```

Result: embedding JSONL contains `embedding_provider` and
`provider_provenance` with deterministic fallback metadata.

Passed:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
uv run foi-o-nz schema-drift
```

Result: examples ok, repository validation ok, and schema drift returned
`ok: true` with warning-level pre-existing top-level drift for unrelated
`core-event`, `reporting-metric`, and `request-profile` schemas.

Passed:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Result: Ruff check passed and `99 files already formatted`.

## Conductor Review

`conductor-review` is not installed on PATH in this workspace, so the review was
performed using the `conductor-review` skill protocol as a manual fallback.

Review inputs:

- `conductor/tracks/max_lancedb_inference_20260702/spec.md`
- `conductor/tracks/max_lancedb_inference_20260702/plan.md`
- `conductor/workflow.md`
- Phase diff from Track 7 start commit `5b985cd`
- Focused provider, embedding, retrieval, agent-policy, example, repo, schema,
  and style checks

Findings applied: none.

Unresolved findings: none.

## Boundaries Verified

- Deterministic feature-hash remains the default provider and records fallback
  provenance.
- Configured MAX/OpenAI-compatible provider selection reports status without
  contacting a live endpoint.
- Missing MAX dependency degrades to deterministic fallback with an explicit
  message.
- Candidate provider outputs cannot assert certified machine-generated legal
  outcomes.
- Embedding records carry provider, model, runtime, fallback, legal-effect, and
  machine-certification metadata.

## External Gates

- Live MAX/local endpoint execution remains a later external gate.
- Native `conductor-review` command: unavailable locally; manual skill-protocol
  review completed.
