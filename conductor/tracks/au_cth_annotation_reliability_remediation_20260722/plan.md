# Plan: AU-CTH annotation reliability remediation

## Phase 1: Preserve and audit the calibration run

- [x] Inventory the codebook, execution frame, blinded packets, role outputs,
      adjudication output, and metric packet with byte counts and SHA-256.
- [x] Move local-only artifacts from ephemeral storage into an approved
      durable restricted store; commit only a non-sensitive manifest.
- [x] Add a verifier that rejects missing artifacts, `/tmp` evidence paths,
      mismatched hashes, synthetic revisions, altered units, and role overlap.
      Commit: `ea23f2b`.
- [x] Recompute the nine-unit diagnostic with explicit label, span, and
      abstention denominators and reconcile the eight-item queue with the two
      primary-label disagreements.
- [ ] Run focused tests and Conductor review for Phase 1.

## Phase 2: Repair the annotation contract

- [ ] Write failing positive and negative tests for a single annotation-output
      schema, target assertion, evidence window, jurisdiction rule, span
      coordinates, null encoding, and abstention behavior.
- [x] Commit `foio-au-pilot-assertion-v0.2.0` with a genuine revision and hash.
      Draft committed at `d45df67`; content SHA-256 is
      `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9`.
      Approved through wrapper commit `c210e39`.
- [ ] Add deterministic validators for packets, role outputs, adjudication,
      disagreement queues, and metric inputs.
- [ ] Add narrow-span and whole-document negative fixtures plus ambiguous
      AU-CTH identity fixtures.
- [ ] Produce Markdown/Mermaid and BPMN 2.0 versions of the repaired workflow.
- [x] Obtain hash-bound human codebook approval before fresh execution.
      Approval wrapper commit: `c210e39`.
- [ ] Run focused and repository contract tests and Conductor review for Phase 2.

## Phase 3: Freeze a fresh holdout

- [ ] Acquire additional rights-eligible authentic AU-CTH records or record
      that the available population cannot support an independent holdout.
- [ ] Apply the registered duplicate clustering rules and exclude every
      calibration cluster from the holdout.
- [ ] Freeze the frame, membership, exclusions, seed, PRNG version, unit order,
      sample-size justification, and finite-population limitation.
- [ ] Obtain exact rights, sample-membership, and execution approvals.
- [ ] Generate two schema-identical blinded packets and verify no extractor or
      peer-label leakage.
- [ ] Run focused tests and Conductor review for Phase 3.

## Phase 4: Execute and evaluate

- [ ] Run two isolated annotator roles and one distinct adjudicator role with
      immutable actor and artifact provenance.
- [ ] Compute confusion tables, agreement, kappa, span metrics, abstention,
      cluster-bootstrap intervals, missingness, and disagreement queues.
- [ ] Evaluate the ontology-pinned extractor against the adjudicated holdout,
      including precision, recall, F1, coverage, provenance completeness, and
      unsafe-inference rate.
- [ ] Produce a maturity-decision packet that applies the preregistered
      thresholds without automatic promotion.
- [ ] Obtain and record the human maturity decision.
- [ ] Run full validation and final Conductor review; archive only if all track
      acceptance criteria and gates are satisfied.
