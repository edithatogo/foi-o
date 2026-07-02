# Plan: Corpus profile and 100-request goldset

## Phase 1: Corpus Intake Contract [checkpoint: f9b4933]

- [x] Task: Audit current manifest intake and request profile coverage (`a7a5f6e`)
    - [x] Review normalisation code, request-profile schema, examples, and docs for source-state handling.
    - [x] Identify missing fixture coverage for live-style archive manifest records.
    - [x] Record repo-local versus live-source proof requirements.
- [x] Task: Write fixture intake tests (`e536bbc`)
    - [x] Add tests for source-state preservation and normalised state mapping.
    - [x] Add tests for JSONL/JSON array archive input variants.
    - [x] Add tests that live-source configuration can fail closed without breaking fixture mode.
- [x] Task: Implement corpus intake hardening (`e536bbc`)
    - [x] Extend or adjust normalisation helpers only where tests identify contract gaps.
    - [x] Ensure provenance fields identify source file, record id, and state mapping basis.
    - [x] Keep external dataset fetches optional and documented.
- [x] Task: Conductor - User Manual Verification 'Corpus Intake Contract' (Protocol in workflow.md) (`f9b4933`)

## Phase 2: Request JSON-LD Profile

- [~] Task: Write request JSON-LD profile validation tests
    - [ ] Validate committed request JSON-LD examples against schema and RDF parse expectations.
    - [ ] Cover missing source-state and provenance fields.
- [~] Task: Implement request profile JSON-LD updates
    - [ ] Align context, examples, and docs with request-profile schema fields.
    - [ ] Keep JSON-LD generation deterministic and fixture-friendly.
- [ ] Task: Conductor - User Manual Verification 'Request JSON-LD Profile' (Protocol in workflow.md)

## Phase 3: Goldset Workflow

- [ ] Task: Write goldset sampling and annotation export tests
    - [ ] Test deterministic 100-request sampling parameters with a smaller fixture fallback.
    - [ ] Test annotation-task outputs include source state, normalised state, confidence, event hints, and evidence references.
- [ ] Task: Implement reproducible goldset workflow
    - [ ] Add or refine CLI/docs for generating 100-request goldsets.
    - [ ] Produce committed small examples that validate without live data.
    - [ ] Document live full-size run commands and external gates.
- [ ] Task: Conductor - User Manual Verification 'Goldset Workflow' (Protocol in workflow.md)

## Phase 4: Corpus Profile Closeout

- [ ] Task: Run corpus profile validation
    - [ ] Run targeted corpus/goldset tests.
    - [ ] Run schema/example validation commands affected by this track.
    - [ ] Update docs with exact commands and expected outputs.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Corpus Profile Closeout' (Protocol in workflow.md)
