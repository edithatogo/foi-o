# Plan: PSC reporting profile and aggregate reports

## Phase 1: Reporting Mapping Baseline

- [~] Task: Audit current PSC mappings and reporting helpers
    - [ ] Review mapping YAML, reporting module, analytics, table contracts, and docs.
    - [ ] Identify missing derivability classifications and fixture coverage.
- [ ] Task: Write reporting mapping tests
    - [ ] Validate mapping records for metric id, definition, derivability, required fields, and exclusions.
    - [ ] Cover non-derivable public-data cases.
- [ ] Task: Implement reporting mapping updates
    - [ ] Update mapping files, schemas, and docs for derivability status.
    - [ ] Keep official-reporting caveats explicit.
- [ ] Task: Conductor - User Manual Verification 'Reporting Mapping Baseline' (Protocol in workflow.md)

## Phase 2: Aggregate Report Generation

- [ ] Task: Write aggregate report tests
    - [ ] Use committed fixtures to produce deterministic aggregate summaries.
    - [ ] Verify warning/caveat fields appear for partial or non-derivable metrics.
- [ ] Task: Implement aggregate report outputs
    - [ ] Add or refine CLI/reporting functions for sample aggregate reports.
    - [ ] Ensure outputs validate against schemas or table contracts.
- [ ] Task: Conductor - User Manual Verification 'Aggregate Report Generation' (Protocol in workflow.md)

## Phase 3: Publication-Safe Reporting Docs

- [ ] Task: Write documentation consistency checks
    - [ ] Verify README/docs do not imply official PSC certification.
    - [ ] Check documented commands match implemented CLI commands.
- [ ] Task: Implement reporting documentation
    - [ ] Document derivable versus non-derivable metrics.
    - [ ] Include sample commands and expected fixture outputs.
- [ ] Task: Conductor - User Manual Verification 'Publication-Safe Reporting Docs' (Protocol in workflow.md)

## Phase 4: Reporting Closeout

- [ ] Task: Run reporting validation
    - [ ] Run reporting, analytics, mapping, schema, and table-contract tests.
    - [ ] Generate sample fixture reports and validate outputs.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Reporting Closeout' (Protocol in workflow.md)
