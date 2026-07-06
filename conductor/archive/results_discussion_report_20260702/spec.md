# Specification: Results, discussion, and conclusion report

## Overview

Create a comprehensive results report that presents what FOI-O NZ produced,
how well the repo-local evidence supports those outputs, what limitations
remain, and what conclusions can be drawn about the ontology-development method.
The report must build on the ontology methods protocol track and prepare the
argument for a journal article.

This track depends on `publication_quality_panel_20260702` and
`ontology_methods_protocol_20260702`. It must consume the protocol's evidence
inventory, claims register, terminology crosswalk, visual asset contract, agent
scorecards, and checklist contracts rather than redefining them.

## Functional Requirements

- Summarise implemented outputs across schemas, ontology, SKOS vocabularies,
  SHACL shapes, mappings, examples, validation commands, event extraction,
  reporting profiles, agent contracts, deterministic retrieval, publication
  metadata, and release evidence.
- Produce tables or structured summaries for ontology terms, schema surfaces,
  validation checks, examples, quality gates, and external gates.
- Generate publication-ready tables and plots from repo-local evidence, including
  inventory counts, validation-command coverage, evidence classification,
  supported/unsupported claims, and external-gate status.
- Generate graph/network diagram assets using the protocol-defined
  Cosmograph-compatible ontology/evidence network data, with static fallbacks for
  the report and later supplement.
- Maintain a generated-asset manifest for report diagrams, plots, tables, and
  graph/network files with captions, alt text/textual equivalents, source
  inputs, generation commands, and provenance.
- Clearly separate results from discussion and conclusion.
- Discuss strengths, limitations, threats to validity, human-certification
  boundaries, public-data limitations, optional dependency behavior, and external
  gates.
- Include a conclusion that is supported only by repo-local evidence.
- Add tests or validation checks that ensure the report remains tied to current
  repository evidence and required sections.
- Run SourceRight/AuthenText-style review gates on the report's source
  provenance, supported claims, and manuscript-facing prose.

## Non-Functional Requirements

- No unsupported claims of legal validity, official reporting, live source
  completeness, model quality, or journal readiness.
- Results must be reproducible from committed files and deterministic commands.
- Tables and claims should be maintainable as the repo evolves.

## Acceptance Criteria

- `docs/25-ontology-results-discussion.md` exists and contains results,
  discussion, limitations, and conclusion sections.
- The report includes or links generated diagrams, plots, and tables, including
  Cosmograph-compatible graph/network assets where graph structure is reported.
- Generated assets include captions, alt text/textual equivalents, provenance,
  and source-input metadata.
- The report references the protocol document and repo-local evidence.
- The report consumes the protocol evidence inventory, claims register, and
  terminology crosswalk.
- Required publication-panel agents score the analysis/results, generated
  artefacts, report, discussion, and conclusion greater than 95/100, or bounded
  blockers are recorded.
- Focused tests validate required sections and cited local paths.
- Repo-local validation passes.

## Out of Scope

- Journal-specific formatting or submission package preparation.
- New live data collection.
- Legal advice or official PSC/Ombudsman reporting claims.
