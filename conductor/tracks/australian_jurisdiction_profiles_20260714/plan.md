# Plan: Australian FOI jurisdiction profiles

## Phase 1: Profile and source contracts

GitHub subissue: [#28](https://github.com/edithatogo/foi-o/issues/28).

- [ ] Task: Write failing tests for jurisdiction identity, bitemporal legal
      sources, provenance, unsupported states, and cross-profile isolation.
- [ ] Task: Define the jurisdiction-neutral profile interface and Australian
      extension registry.
- [ ] Task: Version profile contracts, capability negotiation, migrations, and
      rejection behavior for unknown profile or contract versions.
- [ ] Task: Integrate the `edithatogo/legislation` FOI source-pack manifest.
- [ ] Task: Define guidance, decision, request-example, and rights manifests.
- [ ] Task: Define PIC-compatible identifiers, temporal parameters, fixtures,
      traces, value states, and epistemic status for named consumers.
- [ ] Task: Record RaC Conformance design provenance and verify that PIC remains
      an optional interoperability boundary rather than a runtime dependency.
- [ ] Task: Conductor - User Manual Verification 'Profile and source contracts' (Protocol in workflow.md)

## Phase 2: Commonwealth and NSW pilot

GitHub subissue: [#29](https://github.com/edithatogo/foi-o/issues/29).

- [ ] Task: Build Commonwealth vocabulary, process, clock, review, and source mappings.
- [ ] Task: Build NSW GIPA vocabulary, proactive/informal/formal pathways,
      clock, review, and source mappings.
- [ ] Task: Add positive, negative, historical, and non-equivalence fixtures.
- [ ] Task: Separate observed events, deterministic calculations, interpretive
      mappings, and human-only legal determinations in contracts and tests.
- [ ] Task: Add independent candidate-to-golden fixture promotion packets with
      source, author, reviewer, effective-date, and rights evidence.
- [ ] Task: Validate schema, SHACL, deterministic rule, and NZ regression gates.
- [ ] Task: Run consumer-contract tests for FOI-O, `fyi-archive`,
      `nlp-policy-nz`, and one read-only agent/MCP surface.
- [ ] Task: Conductor - User Manual Verification 'Commonwealth and NSW pilot' (Protocol in workflow.md)

## Phase 3: Empirical validation

GitHub subissue: [#30](https://github.com/edithatogo/foi-o/issues/30).

- [ ] Task: Freeze stratified Commonwealth and NSW example samples.
- [ ] Task: Dual-annotate, adjudicate, and report agreement by label family.
- [ ] Task: Evaluate ontology-pinned extraction and route disagreements to review.
- [ ] Task: Build a deterministic source-triangulation resolver with primary
      source precedence and explicit exception reasons.
- [ ] Task: Freeze the sampling frame, exclusions, unit of analysis, annotation
      codebook, and reliability thresholds before evaluation.
- [ ] Task: Approve or reject pilot profile maturity claims with recorded evidence.
- [ ] Task: Conductor - User Manual Verification 'Empirical validation' (Protocol in workflow.md)

## Phase 4: Pilot decision gate

GitHub subissue: [#31](https://github.com/edithatogo/foi-o/issues/31).

- [ ] Task: Review Commonwealth and NSW contract portability, reliability,
      exception burden, rights coverage, and consumer evidence.
- [ ] Task: Record a human go/no-go decision and any required profile-contract
      revision before expanding jurisdiction scope.
- [ ] Task: Conductor - User Manual Verification 'Pilot decision gate' (Protocol in workflow.md)

## Phase 5: Remaining jurisdiction tranches

GitHub subissue: [#32](https://github.com/edithatogo/foi-o/issues/32).

- [ ] Task: Add and independently gate ACT and Queensland profiles.
- [ ] Task: Add and independently gate Victoria and Western Australia profiles.
- [ ] Task: Add and independently gate South Australia, Tasmania, and Northern Territory profiles.
- [ ] Task: Run per-profile conformance, temporal, rights, and empirical gates.
- [ ] Task: Conductor - User Manual Verification 'Remaining jurisdiction tranches' (Protocol in workflow.md)

## Phase 6: Release evidence and programme closeout

GitHub subissue: [#33](https://github.com/edithatogo/foi-o/issues/33).

- [ ] Task: Run full quality gates and Conductor review.
- [ ] Task: Synchronize issues, dependencies, evidence, and Project 14 status.
- [ ] Task: Generate the versioned release-evidence bundle for downstream
      manuscript and conformance updates.
- [ ] Task: Archive only profiles with complete legal, empirical, and human gates.
- [ ] Task: Conductor - User Manual Verification 'Release evidence and programme closeout' (Protocol in workflow.md)
