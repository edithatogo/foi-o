# Plan: Australian FOI jurisdiction profiles

Execution contract: follow [the deterministic Australian runbook](./less-capable-model-runbook.md)
in packet order. Record exact commands, results, artifacts, source digests, and
commit SHA for every completed packet. Never mark a human gate complete.

## Current status (2026-07-20)

This track and its GitHub issue hierarchy remain active. Profile/source
contract engineering landed in merged PRs #37, #57, #58, and #59, but the
manual verification gate remains open. The Commonwealth/NSW pilot, empirical
validation, go/no-go decision, later jurisdiction tranches, and release
closeout are not complete. The issue links below are the authoritative queues.

| Phase | GitHub issue | Status |
| --- | --- | --- |
| Profile and source contracts | [#28](https://github.com/edithatogo/foi-o/issues/28) | Engineering complete; verification open |
| Commonwealth and NSW pilot | [#29](https://github.com/edithatogo/foi-o/issues/29) | Open |
| Empirical validation | [#30](https://github.com/edithatogo/foi-o/issues/30) | Open |
| Pilot decision gate | [#31](https://github.com/edithatogo/foi-o/issues/31) | Open |
| Remaining jurisdiction tranches | [#32](https://github.com/edithatogo/foi-o/issues/32) | Open |
| Release evidence and closeout | [#33](https://github.com/edithatogo/foi-o/issues/33) | Open |

### Profile-specific reconciliation (2026-07-26)

The programme checkboxes below remain open when either pilot profile is
incomplete. Current evidence is profile-specific:

| Profile | Legal/source contract | Archive/sample | Extraction/annotation | Remaining gate |
| --- | --- | --- | --- | --- |
| AU-CTH | Adapter integrated; bounded source-pack maturity approved in `AU-DEC-07` | Authentic restricted holdout frozen and approved | Reliability and extractor metrics completed; bounded maturity approved; metadata-only NLP handoff integrated at `e4a8cf3` | No remaining Commonwealth prerequisite; all publication, redistribution, training, legal-certification, unbounded-inference, and broader-promotion boundaries remain |
| AU-NSW | Adapter and bounded source pack approved | No non-empty authentic request artifact after three failed CDX attempts | Not started; placeholders prohibited | Supply and approve the authentic request artifact, then freeze and execute the profile-specific protocol |

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

### AU-NSW historical source recovery refinement

- [x] Task: Add explicit URL-index and all-captures Internet Archive CDX modes,
      manual all-captures confirmation, complete-pagination failure evidence,
      and contract tests. (`fyi-archive` `4d410d6`; governed workflow
      `nsw-source-recovery-20260724.md`)
- [x] Task: Commit the exact RightToKnow all-captures CDX request, including
      instance scope, page/runtime caps, endpoint, artifact-only retention, and
      confirmation token. (`599fe4e`; request SHA-256
      `3c9bb6bda4b51ffc60001ee4f230fb6050269adb78a64122b40867ea1c9e06f1`)
- [x] Task: Obtain authorization for and dispatch bounded exact requests.
      GitHub Actions runs `30068038481`, `30075664496`, and `30176570901`
      all failed safely after bounded Internet Archive CDX connection or TLS
      retries. Their 90-day artifacts are negative evidence only and no source
      export was created.
- [x] Task: Validate a non-empty complete CDX export and its raw hash before
      recovery; retain failed, empty, or capped exports as negative evidence.
      (`8002887`; run `30236042144`; artifact SHA-256
      `1034e55f8bdfaddc1aa3ad1c1839aed9d0583641281ddd0dc88eb3a4db6c49b2`;
      CDX SHA-256
      `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`;
      all 26,000 metadata-only classifications remain unresolved pending
      separately authorized authority evidence.)
- [x] Task: Recover only export-listed archived snapshots, classify AU-NSW
      with authority evidence, and validate the normalized source JSONL.
      The amended bounded replay completed successfully with one persistent,
      paced Internet Archive connection.
      Selection SHA-256 is
      `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`;
      all 2,082 captures completed with zero failures. Parser-v3 local
      reprocessing and four-way classification produced 1,578 AU-CTH, 179
      AU-NSW, 115 out-of-scope, and 210 unresolved records. Normalized JSONL
      SHA-256 is
      `3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807`;
      candidate summary SHA-256 is
      `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab`.
      Archive-side validation and the independent FOI-O oracle passed.
      The separately authorized 1,716 exact canonical CDX lookups for the 858
      excluded slugs also completed with zero failures, finding no qualifying
      canonical JSON or HTML capture. Completion candidate SHA-256 is
      `0dafc44c1b871357802282f138bf0e6e9d68f249a171c1d9627809bd928531c8`;
      non-final zero-record replay selection SHA-256 is
      `370a6d84e20a4bd260619209d84098458c9e72acf7e4e6f5cb3465cbaba88bb6`.
      The immutable-manifest approval packet is
      `docs/44-au-rtk-immutable-manifest-approval-packet-2026-07-27.md`.
      See `docs/43-au-rtk-replay-attempt-2026-07-27.md` for the finalized
      restricted-local manifest.
- [x] Task: Obtain a separate hash-bound approval before immutable manifest.
      Approval was received and one restricted-local immutable manifest was
      finalized and independently validated: self-pin SHA-256
      `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c`;
      stored-file SHA-256
      `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393`.
- [ ] Task: Obtain a separate hash-bound approval before empirical-frame
      freeze, annotation, or maturity evaluation.

### Phase 3 review fixes

- [x] Task: Refresh generated maturation inventory counts after adding the
      operator-packet schema. (`ea5565e`; generated summary and coverage matrix
      now record 182 JSON Schema files.)
- [x] Task: Publish a schema-validated operator packet that maps every current
      readiness blocker to its owner issue, required evidence, and human gate.
      (`dad961b`; all 12 blockers are covered exactly once and promotion and
      tranche 5 remain prohibited.)
- [x] Task: Refresh generated ontology inventory evidence, install the declared
      RDF validation extra, and document the source-triangulation v0.2.0
      migration boundary found by whole-suite review. (`f158099`; focused
      ontology, SHACL, readiness, and triangulation review suite: 30 passed.)
- [x] Task: Repair the legacy track's requirements, risk, traceability,
      decisions, outputs, human-gate, workflow, issue, acceptance, closeout,
      and append-only evidence records. (`8a828b4`; required governance files
      parse and the workflow-pair test passes.)
- [x] Task: Refresh generated maturation inventory after recording the
      Commonwealth source-pack approval wrapper. (`e04a9a6`; the canonical
      summary and coverage matrix now record 270 example files.)

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
