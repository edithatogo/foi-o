# Plan: FOI-O V2 empirical implementation

## Phase 1: Reviewed bundle import

- [x] Task: Identify the target repository and preserve the starting state.
- [x] Task: Verify archive safety and SHA-256.
- [x] Task: Validate the bundle and isolated work-package suites.
- [x] Task: Run the conflict-aware bootstrap and retain its report locally.

## Phase 2: Repository-native integration

- [x] Task: Reconcile ADR and numbered-document namespaces.
- [x] Task: Add empirical schemas, positive/negative fixtures, codebooks, contracts, and migrations.
- [x] Task: Integrate reference Pydantic records and public package exports.
- [x] Task: Add native validation for every V2 positive and negative schema fixture.
- [x] Task: Preserve existing `oia_rules`, raw state mapping, and certification boundaries.
- [x] Task: Run native validation and repair integration findings (`a966b3a`).

## Phase 3: Traceability and handoff

- [x] Task: Record final SHAs, validation outcomes, decisions, risks, outputs, and release gates.
- [x] Task: Create focused local commits and git notes without pushing (`a966b3a`).
- [x] Task: Mark repo-local integration complete while retaining human and empirical gates.

## Human and empirical follow-up gates

- [ ] `[HUMAN]` Pin and approve the target revision for upstream review.
- [ ] `[HUMAN]` Approve stable labels, gold fixtures, and official legal mappings.
- [ ] Build an independent `oia_rules` event-time fixture set without reusing authoring data.
- [ ] Populate and review NZ historical source packs and the source-rights registry.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
- [ ] Freeze the empirical sample, dual-annotate, adjudicate, and evaluate reliability.
- [ ] `[HUMAN]` Authorize any issue/PR, dataset, release, or preprint action.
