# Specification: Publication quality panel and checklist contracts

## Overview

Create a reusable publication quality panel for FOI-O NZ publication artifacts.
The panel defines reviewer agents, expert agents, scoring rubrics, scorecard
schemas, iterative improvement loops, reporting-checklist contracts, and
adherence checks. It must be consumed by the protocol, results/report, journal
manuscript, generated artefacts, and supplement tracks.

## Functional Requirements

- Define named review agents and responsibilities:
  - editor;
  - peer reviewer;
  - copy editor;
  - publisher/production editor;
  - ontology/semantic-web expert;
  - OIA/public-administration expert;
  - legal-informatics/source-provenance expert;
  - economist;
  - operations researcher/process-modelling expert;
  - data-engineering/reproducibility expert;
  - visualization/network-analysis expert, including Cosmograph graph review;
  - red-team agent;
  - devil's-advocate agent.
- Define required scoring targets for each artifact category:
  - protocol;
  - analysis/results;
  - generated artefacts, including diagrams, plots, tables, Cosmograph-compatible graph data, and asset manifests;
  - report/discussion/conclusion;
  - manuscript;
  - supplement.
- Require each agent to score each applicable artifact out of 100 and provide
  concise, actionable findings.
- Define an iterative improvement loop:
  - run panel review;
  - record scores and findings;
  - apply high-confidence fixes;
  - rerun panel review;
  - continue until every required agent/artifact score is greater than 95/100 or a bounded blocker is recorded.
- Define machine-readable scorecard and review-output contracts, using repo-local
  JSON/YAML schemas or fixtures.
- Identify relevant reporting/checklist standards during implementation using
  current sources, record retrieval dates, and classify each as required,
  optional, not applicable, or external gate.
- Create machine-readable checklist contracts from selected reporting checklists
  and validate artifact adherence against those contracts.
- Ensure all review/scoring outputs preserve FOI-O NZ boundaries: no legal
  advice, no official PSC/Ombudsman reporting claim, no live-source completeness
  claim, and no autonomous certification of OIA outcomes.

## Non-Functional Requirements

- Review agents are evaluators and critics, not autonomous certifiers.
- Scores must be auditable, reproducible from committed artifacts where possible,
  and tied to artifact versions.
- Checklist contracts must preserve source URL, retrieval date, checklist item
  text, applicability, evidence path, adherence status, score impact, and
  reviewer notes.
- Any live journal/checklist lookup is an external-source retrieval step and must
  be recorded with date and URL.
- The target threshold is strict: every required agent/artifact score must be
  greater than 95, not merely equal to 95.

## Acceptance Criteria

- A panel specification document exists under `docs/` and lists all required
  agents, responsibilities, artifacts, scoring rubrics, loop rules, and pass
  threshold.
- Machine-readable contracts exist for scorecards, panel review outputs,
  checklist source snapshots, checklist item contracts, and checklist adherence
  reports.
- Tests validate the contracts and example scorecard/checklist fixtures.
- The three publication tracks reference this panel track and include panel
  review loops before final artifact readiness.
- At least one example panel scorecard and one example checklist adherence report
  exist as repo-local fixtures.

## Out of Scope

- Claiming that agent scores replace human editorial, peer-review, legal, or
  publisher decisions.
- Performing live journal submission.
- Treating checklist adherence as proof of journal acceptance.
- Creating hidden or non-reproducible scoring criteria.
