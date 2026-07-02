# Plan: OIA process rules and legal-source versioning

## Phase 1: Calendar Contract [checkpoint: d916083]

- [x] Task: Audit current clock helpers and mappings (`e57420c`)
    - [x] Review date helpers, Mojo clock kernels, mappings, examples, and docs.
    - [x] Identify calendar assumptions that are currently hard-coded or undocumented.
- [x] Task: Write working-day calendar tests (`4ed7306`)
    - [x] Cover weekends, NZ public holidays, OIA summer closure, and missing calendar data.
    - [x] Verify warning strings remain explicit and non-certifying.
- [x] Task: Implement calendar support (`4ed7306`)
    - [x] Add fixture-backed calendar data or documented hooks for official calendar input.
    - [x] Keep default behavior deterministic and dependency-light.
- [x] Task: Conductor - User Manual Verification 'Calendar Contract' (Protocol in workflow.md) (`d916083`)

## Phase 2: Source-Versioned References

- [~] Task: Write source-reference validation tests
    - [ ] Validate legislation/guidance mapping records include identifiers, source URLs, version/retrieval dates, and status.
    - [ ] Cover unavailable live-source behavior.
- [~] Task: Implement legal-source versioning
    - [ ] Extend mapping files and docs for source-versioned OIA/Ombudsman references.
    - [ ] Add live-source commands only if they fail closed and cache outputs outside Git by default.
- [ ] Task: Conductor - User Manual Verification 'Source-Versioned References' (Protocol in workflow.md)

## Phase 3: Process Rule Quality Gates

- [ ] Task: Write process-rule quality tests
    - [ ] Cover missing evidence, unsafe certification, stale references, and contradictory status signals.
    - [ ] Verify warnings differentiate repo-local proof from legal certainty.
- [ ] Task: Implement stronger quality gates
    - [ ] Add quality checks and schema/example updates for process-rule references.
    - [ ] Update docs with exact pass/fail examples.
- [ ] Task: Conductor - User Manual Verification 'Process Rule Quality Gates' (Protocol in workflow.md)

## Phase 4: OIA Rules Closeout

- [ ] Task: Run OIA process validation
    - [ ] Run date, state-machine, quality, mapping, and schema tests.
    - [ ] Run available Mojo clock tests or document Modular external gate.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'OIA Rules Closeout' (Protocol in workflow.md)
