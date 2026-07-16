# Plan: FOI-O V2 empirical implementation

Execution contract: follow [the deterministic runbook](./less-capable-model-runbook.md)
one packet at a time. A packet is not complete until its exact commands, exit
codes, outputs, and commit SHA are recorded below.

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

GitHub subissues: [#25](https://github.com/edithatogo/foi-o/issues/25),
[#26](https://github.com/edithatogo/foi-o/issues/26), and
[#27](https://github.com/edithatogo/foi-o/issues/27).

- [~] Export a versioned FOI-O extraction contract for `nlp-policy-nz`, including
  ontology, schema, codebook, provenance, and candidate-status identifiers.
- [x] Define the independently versioned `foi-o` core and jurisdiction-profile
  family contract, including `foi-o-nz` and `foi-o-au-nsw` examples.
  - Evidence: `docs/39-ontology-versioning-and-jurisdiction-profiles.md`;
    `schemas/json/ontology-release-manifest.schema.json`; 54 schema-fixture tests passed.
- [ ] Define contract-version compatibility, capability negotiation, migrations,
  and rejection behavior for unknown revisions.
- [ ] Add consumer-contract tests for FOI-O, `fyi-archive`, `nlp-policy-nz`, and
  one read-only agent/MCP surface.
- [ ] Re-extract the pinned `fyi-archive-nz` snapshot and compare it with the
  initial ontology-based baseline without overwriting raw archive records.
- [ ] `[HUMAN]` Pin and approve the target revision for upstream review.
- [ ] `[HUMAN]` Approve stable labels, gold fixtures, and official legal mappings.
- [ ] Build an independent `oia_rules` event-time fixture set without reusing authoring data.
- [ ] Build deterministic source-triangulation assertions and an explicit human
  exception queue for blocked, conflicting, stale, rights-uncertain, or
  insufficient evidence.
- [ ] Populate and review NZ historical source packs and the source-rights registry.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
- [ ] Freeze the empirical sample, dual-annotate, adjudicate, and evaluate reliability.
- [ ] Generate a versioned release-evidence bundle containing tag/SHA, contract
  versions, capabilities, tests, fixtures, provenance, empirical results,
  exceptions, migrations, and limitations.
- [ ] Trigger the RaC Conformance paper-update workflow only after the release
  bundle is immutable and published.
- [x] `[HUMAN]` Authorize creation of the GitHub issues required to coordinate
  recommended repository changes.
- [ ] `[HUMAN]` Authorize any PR, dataset, release, or preprint action.
