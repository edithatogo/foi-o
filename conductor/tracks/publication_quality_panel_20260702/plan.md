# Plan: Publication quality panel and checklist contracts

## Phase 1: Panel and scoring contract design

- [ ] Task: Define panel agent roles
    - [ ] Create a publication panel document under `docs/`.
    - [ ] Define editor, peer reviewer, copy editor, publisher/production editor, ontology/semantic-web expert, OIA/public-administration expert, legal-informatics/source-provenance expert, economist, operations researcher/process-modelling expert, data-engineering/reproducibility expert, visualization/network-analysis expert, red-team agent, and devil's-advocate agent.
    - [ ] Define which agents must review protocol, analysis/results, generated artefacts, report/discussion/conclusion, manuscript, and supplement outputs.
- [ ] Task: Write scorecard contract tests first
    - [ ] Add focused tests for scorecard and panel-review example fixtures.
    - [ ] Require artifact id, artifact type, artifact version or path, agent id, score out of 100, threshold, pass/fail status, findings, required fixes, residual risks, and review timestamp.
    - [ ] Require pass status only when score is greater than 95.
- [ ] Task: Implement scorecard and panel-review contracts
    - [ ] Add JSON Schema or equivalent contract files for scorecards and panel review summaries.
    - [ ] Add example scorecard fixtures covering passing and failing reviews.
    - [ ] Add validation through existing example/schema validation patterns.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Panel and scoring contract design' (Protocol in workflow.md)

## Phase 2: Checklist discovery and machine-readable contracts

- [ ] Task: Identify relevant reporting and submission checklists
    - [ ] Search current sources for relevant reporting, ontology, methods, research-software, data/software availability, visualization, and journal-specific checklists.
    - [ ] Record source URL, retrieval date, owner/publisher, article type, applicability rationale, and whether each checklist is required, optional, not applicable, or external gate.
    - [ ] Include journal-specific checklist requirements once the target journal is selected.
- [ ] Task: Write checklist contract tests first
    - [ ] Add focused tests for checklist source snapshots, checklist item contracts, and adherence reports.
    - [ ] Require item id, source checklist, item text, applicability, evidence path, adherence status, score impact, reviewer notes, and retrieval metadata.
    - [ ] Require every applicable checklist item to have evidence or a documented blocker.
- [ ] Task: Implement checklist contracts and fixtures
    - [ ] Add machine-readable checklist contract schema or fixture format.
    - [ ] Add at least one example checklist source snapshot and one adherence report fixture.
    - [ ] Add validation commands or tests using repo-local fixtures.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Checklist discovery and machine-readable contracts' (Protocol in workflow.md)

## Phase 3: Review loop integration

- [ ] Task: Define >95/100 improvement loop
    - [ ] Document the review loop: panel review, score capture, high-confidence fix, rerun, and blocker recording.
    - [ ] Require every required agent/artifact score to be greater than 95/100 before artifact readiness.
    - [ ] Define bounded blocker handling for subjective disagreement, unavailable external sources, and journal-only human decisions.
- [ ] Task: Integrate with publication tracks
    - [ ] Update protocol, results/report, and journal-submission tracks to depend on this panel track.
    - [ ] Add panel-review loop tasks to each publication track's readiness phase.
    - [ ] Add checklist-adherence tasks to manuscript and supplement readiness.
- [ ] Task: Verify integration
    - [ ] Run focused panel/checklist tests.
    - [ ] Run `uv run python scripts/validate_examples.py`.
    - [ ] Run Ruff checks on touched tests/scripts.
    - [ ] Run `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Review loop integration' (Protocol in workflow.md)

## Phase 4: Final quality gate and archive

- [ ] Task: Final repo-local verification
    - [ ] Run `uv run pytest -q`.
    - [ ] Run `uv run ruff check src tests scripts`.
    - [ ] Run `uv run ruff format --check src tests scripts`.
    - [ ] Run available Pixi/Mojo checks or record unavailable external gates.
    - [ ] Run final `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Archive completed track
    - [ ] Mark metadata as completed.
    - [ ] Move the track to `conductor/archive/publication_quality_panel_20260702/`.
    - [ ] Update `conductor/tracks.md`.
    - [ ] Commit, attach git notes, and push commits/notes if remote access is available.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final quality gate and archive' (Protocol in workflow.md)
