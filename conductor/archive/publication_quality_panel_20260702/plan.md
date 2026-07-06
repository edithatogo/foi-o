# Plan: Publication quality panel and checklist contracts

## Phase 1: Panel and scoring contract design

- [x] Task: Define panel agent roles (`9093ce9`)
    - [x] Create a publication panel document under `docs/`.
    - [x] Define editor, peer reviewer, copy editor, publisher/production editor, ontology/semantic-web expert, OIA/public-administration expert, legal-informatics/source-provenance expert, economist, operations researcher/process-modelling expert, data-engineering/reproducibility expert, visualization/network-analysis expert, red-team agent, and devil's-advocate agent.
    - [x] Define which agents must review protocol, analysis/results, generated artefacts, report/discussion/conclusion, manuscript, and supplement outputs.
- [x] Task: Write scorecard contract tests first (`9093ce9`)
    - [x] Add focused tests for scorecard and panel-review example fixtures.
    - [x] Require artifact id, artifact type, artifact version or path, agent id, score out of 100, threshold, pass/fail status, findings, required fixes, residual risks, and review timestamp.
    - [x] Require pass status only when score is greater than 95.
- [x] Task: Implement scorecard and panel-review contracts (`9093ce9`)
    - [x] Add JSON Schema or equivalent contract files for scorecards and panel review summaries.
    - [x] Add example scorecard fixtures covering passing and failing reviews.
    - [x] Add validation through existing example/schema validation patterns.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Panel and scoring contract design' (Protocol in workflow.md)

## Phase 2: Checklist discovery and machine-readable contracts

- [x] Task: Identify relevant reporting and submission checklists (`9093ce9`)
    - [x] Search current sources for relevant reporting, ontology, methods, research-software, data/software availability, visualization, and journal-specific checklists.
    - [x] Record source URL, retrieval date, owner/publisher, article type, applicability rationale, and whether each checklist is required, optional, not applicable, or external gate.
    - [x] Include journal-specific checklist requirements once the target journal is selected.
- [x] Task: Write checklist contract tests first (`9093ce9`)
    - [x] Add focused tests for checklist source snapshots, checklist item contracts, and adherence reports.
    - [x] Require item id, source checklist, item text, applicability, evidence path, adherence status, score impact, reviewer notes, and retrieval metadata.
    - [x] Require every applicable checklist item to have evidence or a documented blocker.
- [x] Task: Implement checklist contracts and fixtures (`9093ce9`)
    - [x] Add machine-readable checklist contract schema or fixture format.
    - [x] Add at least one example checklist source snapshot and one adherence report fixture.
    - [x] Add validation commands or tests using repo-local fixtures.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Checklist discovery and machine-readable contracts' (Protocol in workflow.md)

## Phase 3: Review loop integration

- [x] Task: Define >95/100 improvement loop (`9093ce9`)
    - [x] Document the review loop: panel review, score capture, high-confidence fix, rerun, and blocker recording.
    - [x] Require every required agent/artifact score to be greater than 95/100 before artifact readiness.
    - [x] Define bounded blocker handling for subjective disagreement, unavailable external sources, and journal-only human decisions.
- [x] Task: Integrate with publication tracks (`191fa10`)
    - [x] Update protocol, results/report, and journal-submission tracks to depend on this panel track.
    - [x] Add panel-review loop tasks to each publication track's readiness phase.
    - [x] Add checklist-adherence tasks to manuscript and supplement readiness.
- [x] Task: Verify integration (`9093ce9`)
    - [x] Run focused panel/checklist tests.
    - [x] Run `uv run python scripts/validate_examples.py`.
    - [x] Run Ruff checks on touched tests/scripts.
    - [x] Record `conductor-review` as unavailable on PATH; no automated Conductor review fixes applied.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Review loop integration' (Protocol in workflow.md)

## Phase 4: Final quality gate and archive

- [x] Task: Final repo-local verification (`9093ce9`, `05bfe48`)
    - [x] Run `uv run pytest -q`.
    - [x] Run `uv run ruff check src tests scripts`.
    - [x] Run `uv run ruff format --check src tests scripts`.
    - [x] Run available Pixi/Mojo checks or record unavailable external gates.
    - [x] Record `conductor-review` as unavailable on PATH; no automated Conductor review fixes applied.
- [x] Task: Archive completed track
    - [x] Mark metadata as completed.
    - [x] Move the track to `conductor/archive/publication_quality_panel_20260702/`.
    - [x] Update `conductor/tracks.md`.
    - [x] Commit, attach git notes, and push commits/notes if remote access is available.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final quality gate and archive' (Protocol in workflow.md)
