# Plan: Journal submission package

## Phase 1: Journal targeting and requirements

- [ ] Task: Verify dependency completion
    - [ ] Confirm `publication_quality_panel_20260702`, `ontology_methods_protocol_20260702`, and `results_discussion_report_20260702` are archived as complete or explicitly approved as dependency overrides.
    - [ ] Confirm the protocol, results report, evidence inventory, claims register, terminology crosswalk, generated asset contract, scorecard contracts, and checklist contracts exist.
    - [ ] Stop and record a bounded blocker if either dependency is incomplete.
- [ ] Task: Research candidate journals
    - [ ] Search current journal scopes and author instructions.
    - [ ] Consider ontology/semantic-web, digital government, public-sector information, legal informatics, research software, and open-data methods venues.
    - [ ] Record candidate fit, risks, article types, and publication requirements.
- [ ] Task: Select primary target and fallback
    - [ ] Choose one primary target journal.
    - [ ] Choose at least one fallback venue.
    - [ ] Record rationale and external submission gates.
- [ ] Task: Write requirements document
    - [ ] Create `docs/26-journal-target-requirements.md`.
    - [ ] Include retrieval dates, URLs, article type, word limits, figure/table limits, graph/interactive-asset policy, reference style, required statements, data/code policy, supplement policy, and submission checklist.
    - [ ] Include an arXiv requirements snapshot covering TeX/LaTeX packaging, TeX Live versions, source-package root behavior, source-disclosure risks, and human-only upload gates.
    - [ ] Mark human approval and live submission as external gates.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Journal targeting and requirements' (Protocol in workflow.md)

## Phase 2: Manuscript drafting

- [ ] Task: Write manuscript validation tests first
    - [ ] Add focused tests for `docs/27-submission-manuscript.md`.
    - [ ] Require title, abstract, keywords, introduction, methods, results, discussion, conclusion, data/code availability, ethics/legal boundary, author contribution placeholder, conflicts/funding placeholder, and references.
    - [ ] Require local references to protocol and results report.
- [ ] Task: Draft article from repo-local evidence
    - [ ] Create `docs/27-submission-manuscript.md`.
    - [ ] Adapt methods from the protocol and results/discussion from the report.
    - [ ] Align formatting and section structure with target journal requirements.
    - [ ] Include explicit figure, plot, and table callouts in the manuscript text.
    - [ ] Keep all claims bounded to repo-local proof or labelled external gates.
- [ ] Task: Manuscript review and consistency pass
    - [ ] Check journal fit, scope language, word-count expectations, and required statements.
    - [ ] Check terminology consistency with README, protocol, and results report.
    - [ ] Run or document SourceRight-style checks for citations, source provenance, legal/guidance references, and unsupported claims.
    - [ ] Run or document AuthenText-style checks for manuscript-facing prose without changing technical literals.
    - [ ] Run `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Define arXiv readiness tests first
    - [ ] Add focused tests for `docs/30-arxiv-readiness.md`, `schemas/json/arxiv-readiness.schema.json`, and a readiness example.
    - [ ] Require `arxiv-latex-cleaner` as the default sanitizer.
    - [ ] Require TeX Live 2025/`latexmk` compile checks.
    - [ ] Require `arxiv-collector` or `latexpand` only where dependency collection or flattening adds value.
    - [ ] Require ALC-NG to remain optional and second-pass only.
    - [ ] Require source disclosure, secret, metadata, and root-relative path checks.
- [ ] Task: Draft arXiv source-package workflow
    - [ ] Create or update `docs/30-arxiv-readiness.md`.
    - [ ] Create a validated arXiv readiness report for the manuscript/supplement package.
    - [ ] Record commands for `latexmk`, `arxiv-latex-cleaner`, conditional `arxiv-collector` or `latexpand`, optional ALC-NG, and package hygiene scans.
    - [ ] Mark category choice, author metadata, declarations, and live arXiv upload as human-only gates.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Manuscript drafting' (Protocol in workflow.md)

## Phase 3: Supplement drafting

- [ ] Task: Write supplement validation tests first
    - [ ] Add focused tests for `docs/28-submission-supplement.md`.
    - [ ] Require ontology inventory, schema inventory, validation commands, evidence table, external gates, reproducibility notes, boundary statements, generated-asset index, and figure/table/plot references.
    - [ ] Require every referenced generated asset to have a caption, alt text/textual equivalent, source input, generation command, and provenance entry.
- [ ] Task: Draft supplement
    - [ ] Create `docs/28-submission-supplement.md`.
    - [ ] Include detailed method tables and validation evidence.
    - [ ] Link to relevant repo-local files and commands.
- [ ] Task: Generate supplementary assets package
    - [ ] Generate publication tables from the evidence inventory, claims register, schema inventory, ontology/SKOS/SHACL files, examples, and validation commands.
    - [ ] Generate publication plots for artifact composition, validation coverage, claim-support status, and external-gate categories.
    - [ ] Generate graph/network assets from the FOI-O ontology/evidence relationships, preferring Cosmograph-compatible node/edge data and including static fallbacks.
    - [ ] Create a supplement asset index that lists each diagram, plot, table, graph data file, source input, generation command, caption, alt text/textual equivalent, provenance, and intended manuscript/supplement location.
- [ ] Task: Verify article/supplement package
    - [ ] Run focused submission-package tests.
    - [ ] Run examples and documentation checks.
    - [ ] Ensure article and supplement agree on claims, terminology, diagrams, plots, tables, and external gates.
    - [ ] Verify generated supplementary assets are reproducible from committed inputs or explicitly marked as external/tooling gates.
    - [ ] Verify the arXiv readiness report validates and still treats arXiv upload as a human-only gate.
- [ ] Task: Prepare human-only submission handoff
    - [ ] Create a checklist for author details, affiliations, funding, conflicts, ethics/data statements, cover letter, suggested reviewers if required, account upload, and final approval.
    - [ ] Mark every live journal submission step as requiring explicit user approval.
    - [ ] Record any missing human-only information as a bounded external gate.
- [ ] Task: Run publication panel review loop for submission package
    - [ ] Ask required panel agents to score manuscript, supplement, generated artefacts, checklist adherence, and submission-readiness package out of 100.
    - [ ] Record scorecards and actionable findings using the panel contracts.
    - [ ] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [ ] Run checklist adherence checks for selected reporting and journal submission checklists.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Supplement drafting' (Protocol in workflow.md)

## Phase 4: Submission readiness

- [ ] Task: Final package checklist
    - [ ] Ensure target requirements document, article, and supplement satisfy acceptance criteria.
    - [ ] Ensure arXiv readiness documentation and report satisfy the selected source-package pipeline.
    - [ ] Record remaining human tasks such as author details, conflict/funding statements, cover letter, and live upload.
    - [ ] Record any journal-specific files not generated because they require human credentials or approval.
- [ ] Task: Final repo-local verification
    - [ ] Run `uv run pytest -q`.
    - [ ] Run `uv run ruff check src tests scripts`.
    - [ ] Run `uv run ruff format --check src tests scripts`.
    - [ ] Run available Pixi/Mojo checks or record unavailable external gates.
    - [ ] Run final `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Archive completed track
    - [ ] Mark metadata as completed.
    - [ ] Move the track to `conductor/archive/journal_submission_package_20260702/`.
    - [ ] Update `conductor/tracks.md`.
    - [ ] Commit, attach git notes, and push commits/notes if remote access is available.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Submission readiness' (Protocol in workflow.md)
