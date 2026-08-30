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
- [x] Run focused tests and Conductor review for Phase 1. (Review:
      `phase-1-review-2026-08-30.md`)

## Phase 2: Repair the annotation contract

- [x] Write failing positive and negative tests for a single annotation-output
      schema, target assertion, evidence window, jurisdiction rule, span
      coordinates, null encoding, and abstention behavior. Covered in
      `tests/test_au_cth_annotation_output_contract.py`.
- [x] Commit `foio-au-pilot-assertion-v0.2.0` with a genuine revision and hash.
      Draft committed at `d45df67`; content SHA-256 is
      `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9`.
      Approved through wrapper commit `c210e39`.
- [x] Add deterministic validators for packets, role outputs, adjudication,
      disagreement queues, and metric inputs. Implemented in
      `src/foi_o_nz/australian_subset_annotation.py` and covered in
      `tests/test_australian_subset_annotation.py`.
- [x] Add narrow-span and whole-document negative fixtures plus ambiguous
      AU-CTH identity fixtures. Covered in
      `tests/test_au_cth_annotation_output_contract.py`.
- [x] Produce Markdown/Mermaid and BPMN 2.0 versions of the repaired workflow.
      Added `workflow.md` and `workflow.bpmn`; both preserve the approval and
      non-promotion boundaries.
- [x] Obtain hash-bound human codebook approval before fresh execution.
      Approval wrapper commit: `c210e39`.
- [x] Run focused and repository contract tests and Conductor review for Phase 2.
      (Review: `phase-2-review-2026-08-30.md`)

## Phase 3: Freeze a fresh holdout

- [x] Acquire additional rights-eligible authentic AU-CTH records or record
      that the available population cannot support an independent holdout.
      (Recorded in `fresh-holdout-rights-freeze-plan.md`)
- [x] Apply the registered duplicate clustering rules and exclude every
      calibration cluster from the holdout. (Implemented in
      `build_holdout_frame_candidate` in
      `src/foi_o_nz/australian_subset_annotation.py`)
- [x] Freeze the frame, membership, exclusions, seed, PRNG version, unit order,
      sample-size justification, and finite-population limitation.
- [x] Obtain exact rights, sample-membership, and execution approvals.
- [x] Generate two schema-identical blinded packets and verify no extractor or
      peer-label leakage.
- [x] Run focused tests and Conductor review for Phase 3. (Review:
      `phase-3-review-2026-08-30.md`)

## Phase 4: Execute and evaluate

- [x] Run two isolated annotator roles and one distinct adjudicator role with
      immutable actor and artifact provenance.
- [x] Compute confusion tables, agreement, kappa, span metrics, abstention,
      cluster-bootstrap intervals, missingness, and disagreement queues.
      (Implemented in `compute_inter_annotator_metrics` in
      `src/foi_o_nz/australian_subset_annotation.py`)
- [x] Evaluate the ontology-pinned extractor against the adjudicated holdout,
      including precision, recall, F1, coverage, provenance completeness, and
      unsafe-inference rate.
- [x] Produce a maturity-decision packet that applies the preregistered
      thresholds without automatic promotion. (Implemented in
      `build_maturity_decision_candidate` in
      `src/foi_o_nz/australian_subset_annotation.py`)
- [ ] Obtain and record the human maturity decision.
- [x] Run full validation and final Conductor review; archive only if all track
      acceptance criteria and gates are satisfied. (Review:
      `phase-4-review-2026-08-30.md`)
