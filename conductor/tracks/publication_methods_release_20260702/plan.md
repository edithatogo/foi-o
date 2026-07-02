# Plan: Publication, methods paper, and release package

## Phase 1: Release Evidence Package

- [x] Task: Audit release evidence and publication metadata (`0b2c374`)
    - [x] Review README, implementation reports, dataset metadata, reproducibility manifests, and release docs.
    - [x] Identify claims needing repo-local proof or external-gate notes.
- [~] Task: Write release checklist validation tests
    - [ ] Verify release metadata references existing files, commands, schemas, and evidence.
    - [ ] Verify external gates are explicitly labelled.
- [ ] Task: Implement release evidence package
    - [ ] Add or update release checklist, reproducibility commands, and metadata examples.
    - [ ] Keep generated publication payloads out of Git unless reduced to safe fixtures.
- [ ] Task: Conductor - User Manual Verification 'Release Evidence Package' (Protocol in workflow.md)

## Phase 2: Dataset and Repository Publication Metadata

- [ ] Task: Write publication metadata tests
    - [ ] Validate dataset metadata, Croissant-style JSON-LD, Hugging Face card scaffolds, and repository release metadata.
    - [ ] Cover rights/notice boundaries for source archive content.
- [ ] Task: Implement publication metadata updates
    - [ ] Align metadata generators and docs with matured product scope.
    - [ ] Add sample outputs that validate without live publication credentials.
- [ ] Task: Conductor - User Manual Verification 'Dataset and Repository Publication Metadata' (Protocol in workflow.md)

## Phase 3: Methods Paper

- [ ] Task: Write paper evidence checks
    - [ ] Verify cited commands, schemas, examples, and docs exist.
    - [ ] Check claims avoid official-status, legal-advice, and autonomous-decision overreach.
- [ ] Task: Draft methods paper
    - [ ] Add a concise methods paper under docs or publication notes.
    - [ ] Cover motivation, architecture, data model, human-certification boundary, evaluation, limitations, and reproducibility.
- [ ] Task: Conductor - User Manual Verification 'Methods Paper' (Protocol in workflow.md)

## Phase 4: Final Release Closeout

- [ ] Task: Run release validation
    - [ ] Run full repo-local validation, release metadata checks, example validation, and docs checks.
    - [ ] Run publication dry-run checks where available and document live external gates.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Final Release Closeout' (Protocol in workflow.md)
