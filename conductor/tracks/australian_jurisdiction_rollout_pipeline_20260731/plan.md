# Plan: Australian jurisdiction rollout pipeline

Execution is autonomous for repository-owned work. A task stops only when its
next effect crosses a gate declared in `metadata.json`.

## Phase 1 — reconcile and unblock

- [x] Reconcile AU-CTH/AU-NSW completion evidence with the parent Conductor
  track and GitHub issues.
- [x] Audit remaining-jurisdiction dependencies across legislation, fyi-cli,
  fyi-archive, nlp-policy-nz, foi-process, and FOI-O.
- [x] Record platform families, official-source dependencies, rights gates,
  and the dependency-first tranche order.
- [x] Synchronize existing issues; create new issues only for uncovered,
  independently actionable work.

## Phase 2 — pipeline and provenance contracts

- [x] Implement the canonical stage, checkpoint, failure, authorization, and
  provenance schemas.
- [x] Implement a deterministic planner/validator and independent canonical
  digest oracle.
- [x] Add positive and negative fixtures for resume, pin mismatch, stage-order
  violation, population expansion, and unauthorized successor activation.
- [x] Add automatic approval-packet wording and transformation lineage output.

Adversarial review reopened this phase on 2026-07-31. Completion requires
negative tests for absent and duplicate gates, unproduced lineage inputs,
authorization/input mismatch, malformed provenance envelopes, failed
attestations, unpinned codebook cores, and cross-jurisdiction authority
mappings.

## Phase 3 — archive execution adapters

- [ ] Integrate durable first-batch checkpoints and content-addressed artifact
  identities with fyi-archive.
- [ ] Add adaptive Internet Archive pacing, bounded retry classes, checkpoint
  resumption, and exact-URL replacement queues.
- [ ] Add metadata-first classification and bounded full-text selection.

Local, independently reviewed implementation candidates exist for fyi-cli,
fyi-archive, nlp-policy-nz, and foi-process. They remain outside their hosted
default branches pending the explicit push gate recorded in the dependency
register.

## Phase 4 — shared empirical tooling

- [x] Define the Australian authority registry and core codebook contract.
- [x] Define jurisdiction overlay composition and compatibility validation.
- [x] Consolidate frame, sampling, blinded packet, annotation, reliability,
  extractor metric, disagreement, and maturity-packet scripts behind shared
  libraries. (`e70e2aa`)
  - [x] Register immutable run specifications and compatibility pins without
    rewriting historical artifacts. (`e70e2aa`)
  - [x] Add shared frame, duplicate-cluster, and deterministic membership
    contracts. (`e70e2aa`)
  - [x] Add shared blinded-packet, isolated-role, calibration, and adjudication
    contracts. (`e70e2aa`)
  - [x] Add shared reliability, extractor-metric, disagreement, and bounded
    maturity-packet contracts. (`e70e2aa`)
- [x] Enforce a calibration gate before full annotation execution. (`e70e2aa`)

## Phase 5 — remaining jurisdictions

- [ ] Execute the approved dependency-first tranches for ACT, Queensland,
  Victoria, Western Australia, South Australia, Tasmania, and Northern
  Territory.
- [ ] Preserve separate source, rights, temporal, empirical, annotation, and
  maturity evidence for every profile.

## Phase 6 — review

- [x] Run focused and full repository checks.
- [x] Run Conductor review and validate Markdown/Mermaid/BPMN parity.
- [x] Record unresolved external and human gates without weakening them.
