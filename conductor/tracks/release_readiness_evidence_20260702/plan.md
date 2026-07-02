# Plan: Harden release-readiness evidence and kernel fallback validation

## Phase 1: Evidence Baseline [checkpoint: b832c40]

- [x] Task: Audit current readiness and release claims (`d89edbf`)
    - [x] Review README, implementation reports, delta docs, kernel readiness examples, and Mojo audit examples.
    - [x] Identify claims that require repo-local command, test, schema, or manifest evidence.
    - [x] Record gaps directly in the implementation notes or a focused evidence checklist.
- [x] Task: Conductor - User Manual Verification 'Evidence Baseline' (Protocol in workflow.md) (`b832c40`)

## Phase 2: Kernel Fallback Proof [checkpoint: 4563007]

- [x] Task: Write tests for kernel fallback and readiness evidence (`a767556`)
    - [x] Add or extend tests covering Python fallback behavior when native kernels are unavailable.
    - [x] Add or extend tests validating kernel manifest/readiness/audit examples against schemas.
- [x] Task: Implement fallback evidence hardening (`a767556`)
    - [x] Adjust kernel readiness, audit, or manifest generation so claims are deterministic and schema-backed.
    - [x] Keep optional Mojo/MAX availability separate from Python fallback correctness.
- [x] Task: Conductor - User Manual Verification 'Kernel Fallback Proof' (Protocol in workflow.md) (`4563007`)

## Phase 3: Release Gate Documentation [checkpoint: d9e45ea]

- [x] Task: Write tests or checks for release validation documentation (`95c5a24`)
    - [x] Add a lightweight check that documented release commands point at existing scripts, tasks, or files where practical.
    - [x] Confirm examples used in docs remain small committed fixtures.
- [x] Task: Implement release gate documentation updates (`95c5a24`)
    - [x] Update docs with a repeatable release-readiness command sequence.
    - [x] Label external gates such as live services, registry publication, or unavailable Mojo toolchains separately from repo-local proof.
- [x] Task: Conductor - User Manual Verification 'Release Gate Documentation' (Protocol in workflow.md) (`d9e45ea`)

## Phase 4: Final Review and Archive Readiness

- [x] Task: Run final repo-local verification (`f6abd77`)
    - [x] Run `uv run ruff check src tests scripts`.
    - [x] Run `uv run ruff format --check src tests scripts`.
    - [x] Run `uv run pytest -q`.
    - [x] Run available Pixi/Mojo validation tasks, or document the exact unavailable external gate.
- [x] Task: Run Conductor review and apply high-confidence fixes (`f6abd77`)
    - [x] Run `conductor-review` for the track scope. The shell command was unavailable; applied the loaded `conductor-review` skill protocol manually.
    - [x] Apply high-confidence fixes without changing the approved scope.
    - [x] Rerun focused checks affected by fixes.
- [ ] Task: Conductor - User Manual Verification 'Final Review and Archive Readiness' (Protocol in workflow.md)
