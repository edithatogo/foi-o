# Phase 1 Audit: Provider Interface

Date: 2026-07-02

## Reviewed Surfaces

- `src/foi_o_nz/embeddings.py`
- `src/foi_o_nz/retrieval.py`
- `src/foi_o_nz/vector_index.py`
- `src/foi_o_nz/max_client.py`
- `src/foi_o_nz/agent_pack.py`
- CLI commands: `embed-jsonl`, `build-lancedb`, `search-chunks`, `build-agent-pack`
- Tests: `tests/test_embeddings.py`,
  `tests/test_retrieval_redaction_diff_pack_repro.py`
- Schemas/examples: `embedding-record`, `retrieval-result`, `agent-pack`
- Docs: `README.md`, `docs/10-mojo-max-strategy.md`,
  `docs/11-implementation-status.md`, implementation delta notes

## Current State

- Deterministic feature-hash embeddings are implemented and dependency-light.
- Retrieval combines BM25-style lexical scoring with deterministic feature-hash
  vector blending.
- `build-lancedb` materialises embedding JSONL into an optional LanceDB table,
  failing clearly when `lancedb` is not installed.
- `max_client.py` has an optional OpenAI-compatible client builder and bounded
  extraction prompt helper, but no executable provider abstraction.
- Agent packs can include retrieval JSON, but provider/fallback provenance is not
  represented as first-class pack metadata.
- README correctly labels MAX inference as planned and LanceDB as optional.

## Gaps

1. Provider selection is implicit.
   - Embedding records only carry `embedding_model`.
   - There is no stable provider id, runtime id, fallback flag, or error/status
     report for deterministic versus local/MAX provider selection.

2. Optional provider failure is not modelled as a structured result.
   - `build_client()` and `build_lancedb_table()` raise clear `RuntimeError`s,
     but higher-level provider selection cannot return a bounded degraded-mode
     status for tests, agent packs, or operators.

3. LanceDB has table materialisation but no search path.
   - There is no fixture-backed query helper or CLI path that attempts LanceDB
     retrieval and falls back to deterministic retrieval when unavailable.
   - Existing retrieval reports do not record whether semantic/vector lookup was
     deterministic fallback or LanceDB-backed.

4. MAX/local extraction is prompt-only.
   - `draft_extraction_prompt()` contains the right safety boundary, but no
     bounded command/helper validates candidate outputs, records provenance, or
     rejects certified legal outcomes.

5. Agent-pack provenance is incomplete for inference/retrieval.
   - Packs record file paths and counts, not provider/runtime/fallback details.
   - Retrieval results are included as opaque dictionaries without provider
     provenance or human-review requirements.

6. Tests cover deterministic behavior but not provider contracts.
   - Current tests cover hashing, deterministic embeddings, local retrieval, and
     agent-pack boundary text.
   - Missing tests for provider selection, optional dependency absence, MAX/local
     degraded mode, LanceDB query fallback, and unsafe model-output rejection.

## Phase 1 Test Targets

- Deterministic provider selection returns a stable provider contract with
  fallback provenance.
- Configured local/MAX provider reports explicit unavailable/degraded mode when
  optional dependencies or endpoints are absent.
- Embedding records include provider, model, runtime, fallback, and
  non-certification metadata.
- Provider outputs cannot mark release/refusal/redaction/charging/transfer/
  extension/complaint outcomes as certified legal decisions.

## External Gates

- Live MAX/local model serving is an external gate unless a local endpoint is
  available and explicitly configured.
- Live LanceDB is optional. Fixture-mode tests should pass without downloads,
  service keys, GPUs, or MAX runtime.
