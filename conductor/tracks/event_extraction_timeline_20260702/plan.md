# Plan: Event extraction timeline and provenance

## Phase 1: Extraction Baseline [checkpoint: c7059c3]

- [x] Task: Audit current extraction and timeline behavior (`bdef63c`)
    - [x] Review extractors, normalise pipeline, event schemas, quality gates, and evaluation helpers.
    - [x] Identify missing fixture cases for correspondence fields and candidate events.
    - [x] Record certification-boundary assumptions for every candidate event class.
- [x] Task: Write extraction fixture tests (`4418298`)
    - [x] Cover message-like input fields across supported manifest shapes.
    - [x] Cover candidate ExtensionNotified, TransferNotified, ClarificationRequested, ComplaintObserved, decision, release, refusal, and charge signals.
    - [x] Verify candidate dispositive events require human review/certification.
- [x] Task: Implement extraction hardening (`4aa1869`)
    - [x] Adjust rule extractors only to satisfy tested public fixture cases.
    - [x] Preserve conservative matching and confidence/provenance semantics.
- [x] Task: Conductor - User Manual Verification 'Extraction Baseline' (Protocol in workflow.md) (`c7059c3`)

## Phase 2: Timeline Reconstruction

- [~] Task: Write timeline ordering tests
    - [ ] Test deterministic ordering by observed date, source order, and fallback provenance.
    - [ ] Test missing/ambiguous dates produce warnings instead of fabricated precision.
- [ ] Task: Implement timeline reconstruction improvements
    - [ ] Add or refine timeline helpers and output examples.
    - [ ] Ensure timelines retain event ids, request ids, source state, confidence, and evidence references.
- [ ] Task: Conductor - User Manual Verification 'Timeline Reconstruction' (Protocol in workflow.md)

## Phase 3: Evaluation Fixtures

- [ ] Task: Write event evaluation tests
    - [ ] Add safe fixture gold records for observed events and candidate events.
    - [ ] Verify precision/recall/F1 outputs are deterministic and schema-valid.
- [ ] Task: Implement event evaluation updates
    - [ ] Update evaluation docs, examples, and CLI output contracts as needed.
    - [ ] Keep fixture size small enough for committed validation.
- [ ] Task: Conductor - User Manual Verification 'Evaluation Fixtures' (Protocol in workflow.md)

## Phase 4: Event Track Closeout

- [ ] Task: Run event extraction validation
    - [ ] Run targeted event extraction, quality, and evaluation tests.
    - [ ] Run schema/example validation for changed artifacts.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Event Track Closeout' (Protocol in workflow.md)
