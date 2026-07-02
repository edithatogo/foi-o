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

## Phase 2: Source-Versioned References [checkpoint: ec84651]

- [x] Task: Write source-reference validation tests (`fa76fec`)
    - [x] Validate legislation/guidance mapping records include identifiers, source URLs, version/retrieval dates, and status.
    - [x] Cover unavailable live-source behavior.
- [x] Task: Implement legal-source versioning (`fa76fec`)
    - [x] Extend mapping files and docs for source-versioned OIA/Ombudsman references.
    - [x] Add live-source commands only if they fail closed and cache outputs outside Git by default.
- [x] Task: Conductor - User Manual Verification 'Source-Versioned References' (Protocol in workflow.md) (`ec84651`)

## Phase 3: Process Rule Quality Gates [checkpoint: 478e438]

- [x] Task: Write process-rule quality tests (`b622ceb`)
    - [x] Cover missing evidence, unsafe certification, stale references, and contradictory status signals.
    - [x] Verify warnings differentiate repo-local proof from legal certainty.
- [x] Task: Implement stronger quality gates (`b622ceb`)
    - [x] Add quality checks and schema/example updates for process-rule references.
    - [x] Update docs with exact pass/fail examples.
- [x] Task: Conductor - User Manual Verification 'Process Rule Quality Gates' (Protocol in workflow.md) (`478e438`)

## Phase 4: OIA Rules Closeout [checkpoint: 317c6ce]

- [x] Task: Run OIA process validation (`300106b`)
    - [x] Run date, state-machine, quality, mapping, and schema tests.
    - [x] Run available Mojo clock tests or document Modular external gate.
- [x] Task: Run Conductor review and apply high-confidence fixes (`a594412`)
    - [x] Run `conductor-review` for the track scope. Command unavailable; manual fallback recorded in `review.md`.
    - [x] Apply high-confidence fixes and rerun focused checks. CLI metadata fix committed in `c7bbdd9`.
- [x] Task: Conductor - User Manual Verification 'OIA Rules Closeout' (Protocol in workflow.md) (`317c6ce`)
