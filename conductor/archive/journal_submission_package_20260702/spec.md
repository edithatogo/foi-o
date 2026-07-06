# Specification: Journal submission package

## Overview

Identify a relevant journal for the FOI-O NZ ontology and methods outputs,
document the journal requirements, write a submission-ready article draft, and
prepare a supplement. The package must build on the protocol and
results/discussion tracks and must not claim submission, acceptance, or external
review unless a human operator completes those steps.

This track depends on `publication_quality_panel_20260702`,
`ontology_methods_protocol_20260702`, and `results_discussion_report_20260702`.
It must treat live journal submission, author declarations, cover-letter
finalisation, and journal account upload as human approval gates.

## Functional Requirements

- Identify candidate journals that may be interested in ontology engineering,
  semantic web, public-sector information governance, digital government,
  research software, legal informatics, or open-data methods outputs.
- Select a primary target journal and document the rationale, article type,
  scope fit, formatting requirements, word limits, reference style, data/code
  availability requirements, supplementary-material requirements, and submission
  checklist.
- Write an article draft using the completed protocol and results report as
  source material.
- Prepare supplementary material that includes method details, evidence tables,
  validation commands, schema/ontology inventory, external gates, and
  reproducibility notes.
- Prepare an arXiv-ready source-package workflow using `arxiv-latex-cleaner` as
  the default sanitizer, with TeX Live 2025/`latexmk` compile checks and
  conditional dependency collection or flattening where the generated LaTeX
  source needs it.
- Generate a complete supplementary package that includes the supplement text,
  generated tables, generated plots, generated diagrams, Cosmograph-compatible
  graph/network files, static fallbacks, and an asset index.
- Ensure every manuscript and supplement figure, plot, table, and graph asset has
  a caption, alt text/textual equivalent, provenance entry, and source-input
  record.
- Record optional second-pass arXiv source sanitization with ALC-NG only when it
  adds value beyond `arxiv-latex-cleaner` and preserves the compiled output.
- Add repo-local checks that validate required article and supplement sections
  plus cited local paths.
- Keep journal requirements as a documented snapshot with retrieval dates and
  mark final live submission as an external human gate.
- Run SourceRight/AuthenText-style review gates before finalising manuscript and
  supplement outputs.

## Non-Functional Requirements

- Use current journal instructions verified during the track, not stale memory.
- Avoid claims that exceed repo-local evidence.
- Preserve the human-certification, non-legal-advice, and non-official-reporting
  boundaries.
- Keep manuscript and supplement files in plain Markdown as the canonical source
  unless a required journal or arXiv export format is explicitly added and
  validated.

## Acceptance Criteria

- `docs/26-journal-target-requirements.md` records candidate journals, selected
  target, requirements, retrieval dates, and submission gates.
- `docs/27-submission-manuscript.md` contains a complete article draft.
- `docs/28-submission-supplement.md` contains a complete supplement draft.
- `docs/30-arxiv-readiness.md` and a validated arXiv readiness report record the
  source-package pipeline, required commands, optional tools, package checks, and
  human-only upload gates.
- The supplement package includes generated diagrams, plots, tables, graph data,
  and static fallbacks suitable for journal upload or review.
- The supplement package includes a generated-asset manifest suitable for
  reviewer handoff.
- The package includes a human-only submission checklist covering author details,
  declarations, funding/conflicts, cover letter, journal account upload, and
  final approval.
- Required publication-panel agents score the manuscript, supplement, generated
  artefacts, checklist adherence, and submission package greater than 95/100, or
  bounded blockers are recorded.
- Tests validate required sections and repo-local path references.
- Final verification passes or records bounded external gates.

## Out of Scope

- Performing live journal submission without explicit user approval.
- Guaranteeing journal fit, peer-review outcome, or acceptance.
- Creating unsupported live-source, legal, or official-reporting claims.
- Performing final journal or arXiv upload, or claiming that generated supplement
  assets satisfy a journal's production system until the selected journal
  requirements are checked during the track.
