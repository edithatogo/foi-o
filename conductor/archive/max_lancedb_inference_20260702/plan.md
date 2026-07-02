# Plan: MAX and LanceDB bounded inference

## Phase 1: Provider Interface [checkpoint: f7183c4]

- [x] Task: Audit current embeddings, retrieval, and MAX client surfaces (`f6e869b`)
    - [x] Review deterministic embeddings, vector index, retrieval, MAX client, agent packs, and docs.
    - [x] Identify provider-selection and provenance gaps.
- [x] Task: Write provider-selection tests (`e153f66`)
    - [ ] Cover deterministic fallback, configured local/MAX provider, missing optional dependencies, and error reporting.
    - [ ] Verify no provider can emit certified legal outcomes.
- [x] Task: Implement bounded provider interface (`bb12507`)
    - [x] Add or refine provider abstractions only where tests require.
    - [x] Record provider, model, runtime, and fallback provenance in outputs.
- [x] Task: Conductor - User Manual Verification 'Provider Interface' (Protocol in workflow.md) (`f7183c4`)

## Phase 2: LanceDB Retrieval [checkpoint: af497c3]

- [x] Task: Write LanceDB integration tests (`a1d8c65`)
    - [ ] Cover optional dependency absence, fixture embedding inputs, table creation, and query results.
    - [ ] Keep tests deterministic without live downloads or service keys.
- [x] Task: Implement LanceDB semantic retrieval path (`902a74a`)
    - [x] Harden `build-lancedb` and retrieval integration around optional dependencies.
    - [x] Preserve lexical/deterministic fallback when LanceDB is unavailable.
- [x] Task: Conductor - User Manual Verification 'LanceDB Retrieval' (Protocol in workflow.md) (`af497c3`)

## Phase 3: Bounded Extraction Experiments [checkpoint: 97735e7]

- [x] Task: Write inference safety tests (`0fedbb0`)
    - [x] Cover candidate extraction, provenance, review-required flags, and unsafe certification rejection.
    - [x] Verify prompt/docs boundaries for local model experiments.
- [x] Task: Implement bounded inference commands/docs (`7a40e02`)
    - [x] Add commands or docs for optional MAX/local extraction paths.
    - [x] Ensure generated model outputs are excluded from Git unless reduced to safe fixtures.
- [x] Task: Conductor - User Manual Verification 'Bounded Extraction Experiments' (Protocol in workflow.md) (`97735e7`)

## Phase 4: Inference Track Closeout [checkpoint: 7160e3c]

- [x] Task: Run inference validation (`ce58bba`)
    - [x] Run embeddings, retrieval, vector index, agent pack, and optional-provider tests.
    - [x] Run MAX/LanceDB live checks only when dependencies and credentials are available.
- [x] Task: Run Conductor review and apply high-confidence fixes (`72574f3`)
    - [x] Run `conductor-review` for the track scope (manual fallback used because command is unavailable).
    - [x] Apply high-confidence fixes and rerun focused checks.
- [x] Task: Conductor - User Manual Verification 'Inference Track Closeout' (Protocol in workflow.md) (`7160e3c`)
