# Plan: PSC reporting profile and aggregate reports

## Phase 1: Reporting Mapping Baseline [checkpoint: fc5c3df]

- [x] Task: Audit current PSC mappings and reporting helpers (`254410b`)
    - [x] Review mapping YAML, reporting module, analytics, table contracts, and docs.
    - [x] Identify missing derivability classifications and fixture coverage.
- [x] Task: Write reporting mapping tests (`4e067cb`)
    - [x] Validate mapping records for metric id, definition, derivability, required fields, and exclusions.
    - [x] Cover non-derivable public-data cases.
- [x] Task: Implement reporting mapping updates (`243d067`)
    - [x] Update mapping files, schemas, and docs for derivability status.
    - [x] Keep official-reporting caveats explicit.
- [x] Task: Conductor - User Manual Verification 'Reporting Mapping Baseline' (Protocol in workflow.md) (`fc5c3df`)

## Phase 2: Aggregate Report Generation [checkpoint: 89cc1b6]

- [x] Task: Write aggregate report tests (`371304f`)
    - [x] Use committed fixtures to produce deterministic aggregate summaries.
    - [x] Verify warning/caveat fields appear for partial or non-derivable metrics.
- [x] Task: Implement aggregate report outputs (`57be802`)
    - [x] Add or refine CLI/reporting functions for sample aggregate reports.
    - [x] Ensure outputs validate against schemas or table contracts.
- [x] Task: Conductor - User Manual Verification 'Aggregate Report Generation' (Protocol in workflow.md) (`89cc1b6`)

## Phase 3: Publication-Safe Reporting Docs [checkpoint: 8475370]

- [x] Task: Write documentation consistency checks (`8f6f280`)
    - [x] Verify README/docs do not imply official PSC certification.
    - [x] Check documented commands match implemented CLI commands.
- [x] Task: Implement reporting documentation (`83b3fd1`)
    - [x] Document derivable versus non-derivable metrics.
    - [x] Include sample commands and expected fixture outputs.
- [x] Task: Conductor - User Manual Verification 'Publication-Safe Reporting Docs' (Protocol in workflow.md) (`8475370`)

## Phase 4: Reporting Closeout

- [ ] Task: Run reporting validation
    - [ ] Run reporting, analytics, mapping, schema, and table-contract tests.
    - [ ] Generate sample fixture reports and validate outputs.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Reporting Closeout' (Protocol in workflow.md)
