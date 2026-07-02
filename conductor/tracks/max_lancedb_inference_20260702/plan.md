# Plan: MAX and LanceDB bounded inference

## Phase 1: Provider Interface

- [x] Task: Audit current embeddings, retrieval, and MAX client surfaces (`f6e869b`)
    - [x] Review deterministic embeddings, vector index, retrieval, MAX client, agent packs, and docs.
    - [x] Identify provider-selection and provenance gaps.
- [ ] Task: Write provider-selection tests
    - [ ] Cover deterministic fallback, configured local/MAX provider, missing optional dependencies, and error reporting.
    - [ ] Verify no provider can emit certified legal outcomes.
- [ ] Task: Implement bounded provider interface
    - [ ] Add or refine provider abstractions only where tests require.
    - [ ] Record provider, model, runtime, and fallback provenance in outputs.
- [ ] Task: Conductor - User Manual Verification 'Provider Interface' (Protocol in workflow.md)

## Phase 2: LanceDB Retrieval

- [ ] Task: Write LanceDB integration tests
    - [ ] Cover optional dependency absence, fixture embedding inputs, table creation, and query results.
    - [ ] Keep tests deterministic without live downloads or service keys.
- [ ] Task: Implement LanceDB semantic retrieval path
    - [ ] Harden `build-lancedb` and retrieval integration around optional dependencies.
    - [ ] Preserve lexical/deterministic fallback when LanceDB is unavailable.
- [ ] Task: Conductor - User Manual Verification 'LanceDB Retrieval' (Protocol in workflow.md)

## Phase 3: Bounded Extraction Experiments

- [ ] Task: Write inference safety tests
    - [ ] Cover candidate extraction, provenance, review-required flags, and unsafe certification rejection.
    - [ ] Verify prompt/docs boundaries for local model experiments.
- [ ] Task: Implement bounded inference commands/docs
    - [ ] Add commands or docs for optional MAX/local extraction paths.
    - [ ] Ensure generated model outputs are excluded from Git unless reduced to safe fixtures.
- [ ] Task: Conductor - User Manual Verification 'Bounded Extraction Experiments' (Protocol in workflow.md)

## Phase 4: Inference Track Closeout

- [ ] Task: Run inference validation
    - [ ] Run embeddings, retrieval, vector index, agent pack, and optional-provider tests.
    - [ ] Run MAX/LanceDB live checks only when dependencies and credentials are available.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Inference Track Closeout' (Protocol in workflow.md)
