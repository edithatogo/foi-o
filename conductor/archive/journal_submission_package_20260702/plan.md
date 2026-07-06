# Plan: Journal submission package

## Phase 1: Journal targeting and requirements

- [x] Task: Verify dependency completion
    - [x] Confirm `publication_quality_panel_20260702`, `ontology_methods_protocol_20260702`, and `results_discussion_report_20260702` are archived as complete or explicitly approved as dependency overrides.
    - [x] Confirm the protocol, results report, evidence inventory, claims register, terminology crosswalk, generated asset contract, scorecard contracts, and checklist contracts exist.
    - [x] Stop and record a bounded blocker if either dependency is incomplete.
- [x] Task: Research candidate journals
    - [x] Search current journal scopes and author instructions.
    - [x] Consider ontology/semantic-web, digital government, public-sector information, legal informatics, research software, and open-data methods venues.
    - [x] Record candidate fit, risks, article types, and publication requirements.
- [x] Task: Select primary target and fallback
    - [x] Choose one primary target journal.
    - [x] Choose at least one fallback venue.
    - [x] Record rationale and external submission gates.
- [x] Task: Write requirements document
    - [x] Create `docs/26-journal-target-requirements.md`.
    - [x] Include retrieval dates, URLs, article type, word limits, figure/table limits, graph/interactive-asset policy, reference style, required statements, data/code policy, supplement policy, and submission checklist.
    - [x] Include an arXiv requirements snapshot covering TeX/LaTeX packaging, TeX Live versions, source-package root behavior, source-disclosure risks, and human-only upload gates.
    - [x] Mark human approval and live submission as external gates.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Journal targeting and requirements' (Protocol in workflow.md)

## Phase 2: Manuscript drafting

- [x] Task: Write manuscript validation tests first
    - [x] Add focused tests for `docs/27-submission-manuscript.md`.
    - [x] Require title, abstract, keywords, introduction, methods, results, discussion, conclusion, data/code availability, ethics/legal boundary, author contribution placeholder, conflicts/funding placeholder, and references.
    - [x] Require local references to protocol and results report.
- [x] Task: Draft article from repo-local evidence
    - [x] Create `docs/27-submission-manuscript.md`.
    - [x] Adapt methods from the protocol and results/discussion from the report.
    - [x] Align formatting and section structure with target journal requirements.
    - [x] Include explicit figure, plot, and table callouts in the manuscript text.
    - [x] Keep all claims bounded to repo-local proof or labelled external gates.
- [x] Task: Manuscript review and consistency pass
    - [x] Check journal fit, scope language, word-count expectations, and required statements.
    - [x] Check terminology consistency with README, protocol, and results report.
    - [x] Run or document SourceRight-style checks for citations, source provenance, legal/guidance references, and unsupported claims.
    - [x] Run or document AuthenText-style checks for manuscript-facing prose without changing technical literals.
    - [x] Run `conductor-review` if available and apply high-confidence fixes.
- [x] Task: Define arXiv readiness tests first
    - [x] Add focused tests for `docs/30-arxiv-readiness.md`, `schemas/json/arxiv-readiness.schema.json`, and a readiness example.
    - [x] Require `arxiv-latex-cleaner` as the default sanitizer.
    - [x] Require TeX Live 2025/`latexmk` compile checks.
    - [x] Require `arxiv-collector` or `latexpand` only where dependency collection or flattening adds value.
    - [x] Require ALC-NG to remain optional and second-pass only.
    - [x] Require source disclosure, secret, metadata, and root-relative path checks.
- [x] Task: Draft arXiv source-package workflow
    - [x] Create or update `docs/30-arxiv-readiness.md`.
    - [x] Create a validated arXiv readiness report for the manuscript/supplement package.
    - [x] Record commands for `latexmk`, `arxiv-latex-cleaner`, conditional `arxiv-collector` or `latexpand`, optional ALC-NG, and package hygiene scans.
    - [x] Mark category choice, author metadata, declarations, and live arXiv upload as human-only gates.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Manuscript drafting' (Protocol in workflow.md)

## Phase 3: Supplement drafting

- [x] Task: Write supplement validation tests first
    - [x] Add focused tests for `docs/28-submission-supplement.md`.
    - [x] Require ontology inventory, schema inventory, validation commands, evidence table, external gates, reproducibility notes, boundary statements, generated-asset index, and figure/table/plot references.
    - [x] Require every referenced generated asset to have a caption, alt text/textual equivalent, source input, generation command, and provenance entry.
- [x] Task: Draft supplement
    - [x] Create `docs/28-submission-supplement.md`.
    - [x] Include detailed method tables and validation evidence.
    - [x] Link to relevant repo-local files and commands.
- [x] Task: Generate supplementary assets package
    - [x] Generate publication tables from the evidence inventory, claims register, schema inventory, ontology/SKOS/SHACL files, examples, and validation commands.
    - [x] Generate publication plots for artifact composition, validation coverage, claim-support status, and external-gate categories.
    - [x] Generate graph/network assets from the FOI-O ontology/evidence relationships, preferring Cosmograph-compatible node/edge data and including static fallbacks.
    - [x] Create a supplement asset index that lists each diagram, plot, table, graph data file, source input, generation command, caption, alt text/textual equivalent, provenance, and intended manuscript/supplement location.
- [x] Task: Verify article/supplement package
    - [x] Run focused submission-package tests.
    - [x] Run examples and documentation checks.
    - [x] Ensure article and supplement agree on claims, terminology, diagrams, plots, tables, and external gates.
    - [x] Verify generated supplementary assets are reproducible from committed inputs or explicitly marked as external/tooling gates.
    - [x] Verify the arXiv readiness report validates and still treats arXiv upload as a human-only gate.
- [x] Task: Prepare human-only submission handoff
    - [x] Create a checklist for author details, affiliations, funding, conflicts, ethics/data statements, cover letter, suggested reviewers if required, account upload, and final approval.
    - [x] Mark every live journal submission step as requiring explicit user approval.
    - [x] Record any missing human-only information as a bounded external gate.
- [x] Task: Run publication panel review loop for submission package
    - [x] Ask required panel agents to score manuscript, supplement, generated artefacts, checklist adherence, and submission-readiness package out of 100.
    - [x] Record scorecards and actionable findings using the panel contracts.
    - [x] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [x] Run checklist adherence checks for selected reporting and journal submission checklists.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Supplement drafting' (Protocol in workflow.md)

## Phase 4: Submission readiness

- [x] Task: Final package checklist
    - [x] Ensure target requirements document, article, and supplement satisfy acceptance criteria.
    - [x] Ensure arXiv readiness documentation and report satisfy the selected source-package pipeline.
    - [x] Record remaining human tasks such as author details, conflict/funding statements, cover letter, and live upload.
    - [x] Record any journal-specific files not generated because they require human credentials or approval.
- [x] Task: Final repo-local verification
    - [x] Run `uv run pytest -q`.
    - [x] Run `uv run ruff check src tests scripts`.
    - [x] Run `uv run ruff format --check src tests scripts`.
    - [x] Run available Pixi/Mojo checks or record unavailable external gates.
    - [x] Run final `conductor-review` if available and apply high-confidence fixes.
- [x] Task: Archive completed track
    - [x] Mark metadata as completed.
    - [x] Move the track to `conductor/archive/journal_submission_package_20260702/`.
    - [x] Update `conductor/tracks.md`.
    - [x] Commit, attach git notes, and push commits/notes if remote access is available.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Submission readiness' (Protocol in workflow.md)
