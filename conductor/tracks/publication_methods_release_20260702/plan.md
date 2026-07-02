# Plan: Publication, methods paper, and release package

## Phase 1: Release Evidence Package [checkpoint: 58b100d]

- [x] Task: Audit release evidence and publication metadata (`0b2c374`)
    - [x] Review README, implementation reports, dataset metadata, reproducibility manifests, and release docs.
    - [x] Identify claims needing repo-local proof or external-gate notes.
- [x] Task: Write release checklist validation tests (`7436c21`)
    - [x] Verify release metadata references existing files, commands, schemas, and evidence.
    - [x] Verify external gates are explicitly labelled.
- [x] Task: Implement release evidence package (`92b82a4`)
    - [x] Add or update release checklist, reproducibility commands, and metadata examples.
    - [x] Keep generated publication payloads out of Git unless reduced to safe fixtures.
- [x] Task: Conductor - User Manual Verification 'Release Evidence Package' (Protocol in workflow.md) (`58b100d`)

## Phase 2: Dataset and Repository Publication Metadata [checkpoint: 7941c01]

- [x] Task: Write publication metadata tests (`ac92d09`)
    - [x] Validate dataset metadata, Croissant-style JSON-LD, Hugging Face card scaffolds, and repository release metadata.
    - [x] Cover rights/notice boundaries for source archive content.
- [x] Task: Implement publication metadata updates (`78f30d2`)
    - [x] Align metadata generators and docs with matured product scope.
    - [x] Add sample outputs that validate without live publication credentials.
- [x] Task: Conductor - User Manual Verification 'Dataset and Repository Publication Metadata' (Protocol in workflow.md) (`7941c01`)

## Phase 3: Methods Paper

- [x] Task: Write paper evidence checks (`b0b1c2e`)
    - [x] Verify cited commands, schemas, examples, and docs exist.
    - [x] Check claims avoid official-status, legal-advice, and autonomous-decision overreach.
- [x] Task: Draft methods paper (`6245088`)
    - [x] Add a concise methods paper under docs or publication notes.
    - [x] Cover motivation, architecture, data model, human-certification boundary, evaluation, limitations, and reproducibility.
- [ ] Task: Conductor - User Manual Verification 'Methods Paper' (Protocol in workflow.md)

## Phase 4: Final Release Closeout

- [ ] Task: Run release validation
    - [ ] Run full repo-local validation, release metadata checks, example validation, and docs checks.
    - [ ] Run publication dry-run checks where available and document live external gates.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Final Release Closeout' (Protocol in workflow.md)
