# Plan: Results, discussion, and conclusion report

## Phase 1: Results evidence model

- [x] Task: Verify dependency completion
    - [x] Confirm `publication_quality_panel_20260702` is archived as complete or explicitly approved as a dependency override.
    - [x] Confirm `ontology_methods_protocol_20260702` is archived as complete or explicitly approved as a dependency override.
    - [x] Confirm the protocol, evidence inventory, claims register, terminology crosswalk, visual asset contract, scorecard contracts, and checklist contracts exist.
    - [x] Stop and record a bounded blocker if the dependency is incomplete.
- [x] Task: Define report evidence contract
    - [x] Identify result categories from the protocol, README, implementation status, schemas, ontology, SHACL, vocab, mappings, tests, examples, and release evidence.
    - [x] Decide which metrics can be counted deterministically from repo-local files.
    - [x] Mark non-derivable claims as limitations or external gates.
    - [x] Consume `docs/24-ontology-methods-evidence-inventory.md` and `docs/24-ontology-claims-register.md` as source-of-truth inputs.
- [x] Task: Write report validation tests first
    - [x] Add focused tests for `docs/25-ontology-results-discussion.md`.
    - [x] Require results, discussion, limitations, conclusion, and evidence sections.
    - [x] Require cited repo-local paths, generated table references, generated plot references, and graph/network asset references to resolve.
- [x] Task: Create report scaffold
    - [x] Draft `docs/25-ontology-results-discussion.md`.
    - [x] Add initial result categories and evidence tables.
    - [x] Link to `docs/24-ontology-methods-protocol.md`.
- [x] Task: Implement report asset generation plan
    - [x] Generate deterministic tables for ontology/schema/SHACL/SKOS inventories, validation evidence, claim support, and external gates.
    - [x] Generate deterministic plots for inventory composition and validation/evidence coverage.
    - [x] Generate Cosmograph-compatible graph/network data for ontology/evidence relationships plus static report fallbacks.
    - [x] Generate or update an asset manifest with captions, alt text/textual equivalents, source inputs, generation commands, and provenance.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Results evidence model' (Protocol in workflow.md)

## Phase 2: Results and discussion writing

- [x] Task: Populate results
    - [x] Summarise implemented ontology/schema/vocabulary/SHACL surfaces.
    - [x] Summarise validation and quality-gate evidence.
    - [x] Summarise agent-boundary, reporting, retrieval, and publication surfaces.
    - [x] Embed or link generated diagrams, plots, and tables in the results narrative.
- [x] Task: Develop discussion
    - [x] Discuss strengths of schema-first and repo-local validation.
    - [x] Discuss public-data limitations, source-version limits, optional dependency limits, and human-certification boundaries.
    - [x] Discuss generalisability to other FOI/OIA jurisdictions without overclaiming.
- [x] Task: Apply report source/prose review
    - [x] Run or document SourceRight-style checks for source provenance and unsupported claims.
    - [x] Run or document AuthenText-style review for low-density manuscript prose cleanup.
    - [x] Update the claims register if any result or discussion claim requires qualification.
- [x] Task: Write supported conclusion
    - [x] State what the repo demonstrates.
    - [x] State what remains external or future work.
    - [x] Preserve non-legal-advice and non-official-reporting caveats.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Results and discussion writing' (Protocol in workflow.md)

## Phase 3: Report verification and readiness

- [x] Task: Verify report consistency
    - [x] Run focused report tests.
    - [x] Run `uv run python scripts/validate_examples.py`.
    - [x] Run relevant release/documentation tests.
    - [x] Verify generated diagrams, plots, tables, and graph/network data are reproducible from committed inputs.
    - [x] Verify every generated asset referenced in the report has a manifest entry, caption, and alt text/textual equivalent.
- [x] Task: Run publication panel review loop for report artifacts
    - [x] Ask required panel agents to score analysis/results, generated artefacts, report/discussion/conclusion, plots, tables, diagrams, graph data, and asset manifest out of 100.
    - [x] Record scorecards and actionable findings using the panel contracts.
    - [x] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [x] Run checklist adherence checks applicable to results reporting and discussion.
- [x] Task: Final repo-local verification
    - [x] Run `uv run pytest -q`.
    - [x] Run `uv run ruff check src tests scripts`.
    - [x] Run `uv run ruff format --check src tests scripts`.
    - [x] Run available Pixi/Mojo checks or record unavailable external gates.
    - [x] Run `conductor-review` if available and apply high-confidence fixes.
- [x] Task: Archive completed track
    - [x] Mark metadata as completed.
    - [x] Move the track to `conductor/archive/results_discussion_report_20260702/`.
    - [x] Update `conductor/tracks.md`.
    - [x] Commit, attach git notes, and push commits/notes if remote access is available.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Report verification and readiness' (Protocol in workflow.md)
