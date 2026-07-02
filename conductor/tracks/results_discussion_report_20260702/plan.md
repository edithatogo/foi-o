# Plan: Results, discussion, and conclusion report

## Phase 1: Results evidence model

- [ ] Task: Verify dependency completion
    - [ ] Confirm `publication_quality_panel_20260702` is archived as complete or explicitly approved as a dependency override.
    - [ ] Confirm `ontology_methods_protocol_20260702` is archived as complete or explicitly approved as a dependency override.
    - [ ] Confirm the protocol, evidence inventory, claims register, terminology crosswalk, visual asset contract, scorecard contracts, and checklist contracts exist.
    - [ ] Stop and record a bounded blocker if the dependency is incomplete.
- [ ] Task: Define report evidence contract
    - [ ] Identify result categories from the protocol, README, implementation status, schemas, ontology, SHACL, vocab, mappings, tests, examples, and release evidence.
    - [ ] Decide which metrics can be counted deterministically from repo-local files.
    - [ ] Mark non-derivable claims as limitations or external gates.
    - [ ] Consume `docs/24-ontology-methods-evidence-inventory.md` and `docs/24-ontology-claims-register.md` as source-of-truth inputs.
- [ ] Task: Write report validation tests first
    - [ ] Add focused tests for `docs/25-ontology-results-discussion.md`.
    - [ ] Require results, discussion, limitations, conclusion, and evidence sections.
    - [ ] Require cited repo-local paths, generated table references, generated plot references, and graph/network asset references to resolve.
- [ ] Task: Create report scaffold
    - [ ] Draft `docs/25-ontology-results-discussion.md`.
    - [ ] Add initial result categories and evidence tables.
    - [ ] Link to `docs/24-ontology-methods-protocol.md`.
- [ ] Task: Implement report asset generation plan
    - [ ] Generate deterministic tables for ontology/schema/SHACL/SKOS inventories, validation evidence, claim support, and external gates.
    - [ ] Generate deterministic plots for inventory composition and validation/evidence coverage.
    - [ ] Generate Cosmograph-compatible graph/network data for ontology/evidence relationships plus static report fallbacks.
    - [ ] Generate or update an asset manifest with captions, alt text/textual equivalents, source inputs, generation commands, and provenance.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Results evidence model' (Protocol in workflow.md)

## Phase 2: Results and discussion writing

- [ ] Task: Populate results
    - [ ] Summarise implemented ontology/schema/vocabulary/SHACL surfaces.
    - [ ] Summarise validation and quality-gate evidence.
    - [ ] Summarise agent-boundary, reporting, retrieval, and publication surfaces.
    - [ ] Embed or link generated diagrams, plots, and tables in the results narrative.
- [ ] Task: Develop discussion
    - [ ] Discuss strengths of schema-first and repo-local validation.
    - [ ] Discuss public-data limitations, source-version limits, optional dependency limits, and human-certification boundaries.
    - [ ] Discuss generalisability to other FOI/OIA jurisdictions without overclaiming.
- [ ] Task: Apply report source/prose review
    - [ ] Run or document SourceRight-style checks for source provenance and unsupported claims.
    - [ ] Run or document AuthenText-style review for low-density manuscript prose cleanup.
    - [ ] Update the claims register if any result or discussion claim requires qualification.
- [ ] Task: Write supported conclusion
    - [ ] State what the repo demonstrates.
    - [ ] State what remains external or future work.
    - [ ] Preserve non-legal-advice and non-official-reporting caveats.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Results and discussion writing' (Protocol in workflow.md)

## Phase 3: Report verification and readiness

- [ ] Task: Verify report consistency
    - [ ] Run focused report tests.
    - [ ] Run `uv run python scripts/validate_examples.py`.
    - [ ] Run relevant release/documentation tests.
    - [ ] Verify generated diagrams, plots, tables, and graph/network data are reproducible from committed inputs.
    - [ ] Verify every generated asset referenced in the report has a manifest entry, caption, and alt text/textual equivalent.
- [ ] Task: Run publication panel review loop for report artifacts
    - [ ] Ask required panel agents to score analysis/results, generated artefacts, report/discussion/conclusion, plots, tables, diagrams, graph data, and asset manifest out of 100.
    - [ ] Record scorecards and actionable findings using the panel contracts.
    - [ ] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [ ] Run checklist adherence checks applicable to results reporting and discussion.
- [ ] Task: Final repo-local verification
    - [ ] Run `uv run pytest -q`.
    - [ ] Run `uv run ruff check src tests scripts`.
    - [ ] Run `uv run ruff format --check src tests scripts`.
    - [ ] Run available Pixi/Mojo checks or record unavailable external gates.
    - [ ] Run `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Archive completed track
    - [ ] Mark metadata as completed.
    - [ ] Move the track to `conductor/archive/results_discussion_report_20260702/`.
    - [ ] Update `conductor/tracks.md`.
    - [ ] Commit, attach git notes, and push commits/notes if remote access is available.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Report verification and readiness' (Protocol in workflow.md)
