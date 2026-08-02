# Autonomous remaining-track execution queue

Updated: 2026-08-02

## Operating rule

Continue repository-local work autonomously in dependency order. Use isolated
subagents for disjoint track reviews, tests, documentation, and fixture work.
Use a single integrator for shared Conductor records. Do not push, merge,
publish, release, retrieve governed sources, alter approved populations, or
promote profiles without the exact gate for that action.

## Priority and dependency sequence

### Lane 0 — cross-track inventory and review

Inspect every active track, normalize its next unchecked task, identify shared
files and external gates, and update only the relevant track ledger. This lane
is read-only until an integrator assigns a disjoint write set.

### Lane 1 — safe local contract work (parallel)

- `au_cth_annotation_reliability_remediation_20260722`: finish packet/output
  validators, negative fixtures, Markdown/Mermaid/BPMN parity, and focused
  validation. Stop before authentic-source acquisition or annotation gates.
- `australian_jurisdiction_profiles_20260714`: finish jurisdiction-neutral
  contracts, source-pack manifests, capability negotiation, and schema/SHACL
  fixtures. Keep runtime activation and empirical claims gated.
- `australian_jurisdiction_rollout_pipeline_20260731`: implement durable
  checkpoint, pacing, retry, metadata-first classification, and validator
  contracts without live capture or replay.
- `foi_o_v2_empirical_implementation_20260714`: perform only the bounded local
  source recovery plan; stop if the approved payloads are not recoverable.

Current integration evidence: legislation PR #106 is merged at its approved
exact head. fyi-cli #286, nlp-policy-nz #235, and foi-process #97 are in draft
review with required checks passing. fyi-archive #327 is in draft review with
all functional/protected checks passing except Codecov patch coverage
(73.25% against the unchanged 90% threshold); the next safe action is focused
coverage additions, not a threshold exception or merge.

### Lane 2 — programme quality and registry work (parallel)

- `global_context_runtime_hardening`: verify fail-closed context compilation
  and record any remaining external gate.
- `ontology_registry_and_semantic_quality`: validate registry, namespace, and
  semantic-quality evidence; do not promote ontology or profiles.
- `testing_scale_and_technology_radar`: run local requirements and quality
  checks; keep unavailable services as explicit external gates.
- `dynamic_versioning_and_release_governance`: validate versioning contracts;
  do not create a release or tag.

### Lane 3 — evidence and maturity preparation

- `jurisdiction_onboarding_and_capability_maturity`: reconcile owner tracks and
  tranche dependencies; do not mark jurisdictions complete without evidence.
- `paper_global_impact_and_reproducibility`: prepare local reproducibility and
  impact evidence only; do not submit or update a paper.

### Lane 4 — human-gate closeout

Use `conductor/human-gate-closeout-plan.md` as the shared gate register. Prepare
promotion, release, publication, redistribution, and external-mutation packets
in dependency order, but stop before each accountable action. Exact heads,
hashes, rights, destinations, and check receipts must be refreshed immediately
before requesting approval.

## Required subagent protocol

Each subagent receives one track and a disjoint write set. It must:

1. Read `AGENTS.md`, the track plan, metadata, workflow, and relevant gates.
2. Report the next task, dependencies, exact files, and blocker evidence.
3. Implement only repository-local work authorized by the track.
4. Run focused validation and attach a git note to its task commit.
5. Return the commit SHA, changed files, validation, and remaining gates.

The integrator reviews each result, runs cross-track validation, updates
`conductor/tracks.md`, track metadata, plan status, decisions, risks, and
traceability, and prevents overlapping edits.

## Stop conditions and contingencies

- Missing source bytes: follow
  `tracks/foi_o_v2_empirical_implementation_20260714/source-recovery-plan.md`.
  Prefer original recovery, then controlled backup, then a fresh authorization
  for a replacement source. Never substitute silently.
- Hosted checks, remote repositories, credentials, or external registration:
  record the exact gate and continue local work; do not infer completion.
- Rights, sample membership, annotation, maturity, publication, release, or
  legal decisions: prepare the approval packet and stop at that gate.
- Shared-file conflict or unclear design choice: pause the affected lane,
  record options and rationale in the owning track, and continue disjoint lanes.
- Two failed bounded repair attempts for the same validation failure: retain
  evidence and present the decision with recommended next action.

## Recommended execution order

1. Complete the Lane 0 inventory and reconcile the active queue.
2. Run Lane 1 and Lane 2 in parallel using isolated subagents.
3. Integrate and review each completed local slice.
4. Resolve source-recovery and other external evidence gates only when exact
   approved inputs are available.
5. Run Lane 3 preparation after its evidence dependencies are stable.
6. Produce a consolidated readiness packet. Keep all external actions pending
   until separately authorized.
