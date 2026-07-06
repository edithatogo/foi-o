# Specification: Ontology methods protocol

## Overview

Create a publication-quality protocol that describes how the FOI-O NZ ontology,
schemas, vocabularies, SHACL shapes, process mappings, and validation evidence
are developed from repository-local materials. The protocol must be suitable as
a methods-forward publication artifact and as the source document for the later
results/discussion and journal-submission tracks.

This track depends on `publication_quality_panel_20260702` and must use its
agent scorecards, >95/100 review loop, and checklist contracts before protocol
readiness.

## Functional Requirements

- Identify and catalogue the repo-local inputs used to develop the ontology,
  including roadmap/backlog materials, schemas, vocabularies, mappings, examples,
  prompts, tests, release evidence, and Conductor archive records.
- Describe the ontology development method in a reproducible sequence:
  domain scoping, source selection, concept extraction, state/event modelling,
  controlled vocabulary design, schema alignment, RDF/OWL modelling, SHACL
  constraint design, validation, quality gates, and release evidence.
- Explicitly document human-certification boundaries and the non-legal-advice
  status of all process-support outputs.
- Distinguish repo-local evidence from external gates such as live FYI/archive
  retrieval, NZ Legislation/Ombudsman live source refresh, registry publication,
  and journal submission.
- Produce a protocol document under `docs/` with clear sections for background,
  objectives, materials, methods, validation, governance, limitations,
  reproducibility, and planned analysis/reporting.
- Produce shared publication source artifacts consumed by later tracks:
  `docs/24-ontology-methods-evidence-inventory.md`,
  `docs/24-ontology-claims-register.md`, and a source/bibliography register
  with retrieval dates and repo-local/external-gate classifications.
- Produce a terminology crosswalk covering FYI/Alaveteli source states, FOI-O NZ
  request states, event types, assertion statuses, legal-source terms,
  validation surfaces, and human-certification terms.
- Define reproducible visual-asset inputs for the publication package, including
  a Cosmograph-compatible ontology/evidence network dataset with node and edge
  records, plus a static fallback diagram format for readers who cannot run
  interactive graph tooling.
- Define the required tables and plots that later tracks must generate from
  repo-local evidence, including inventory counts, validation coverage, evidence
  status, and external-gate summaries.
- Require every publication asset to carry a caption, alt text or textual
  equivalent, source inputs, generation command, and provenance entry so the
  supplement can be reviewed without hidden context.
- Add supporting tests or validation scripts that ensure cited repo-local paths
  and required protocol sections remain present.

## Non-Functional Requirements

- Use concise scholarly technical prose without overstating validation claims.
- Preserve all legal and public-sector caveats already established in the repo.
- Avoid live external calls unless they are explicitly recorded as external
  gates.
- Keep generated or temporary evidence outside version control unless it is a
  small committed fixture.

## Acceptance Criteria

- `docs/24-ontology-methods-protocol.md` exists and is publication-quality.
- `docs/24-ontology-methods-evidence-inventory.md` and
  `docs/24-ontology-claims-register.md` exist and are linked from the protocol.
- A terminology crosswalk exists and is linked from the protocol.
- The protocol defines required diagrams, plots, tables, and supplement inputs,
  including Cosmograph-compatible graph/network data.
- The protocol defines a generated-asset manifest contract covering captions,
  alt text, source inputs, commands, and provenance.
- Required publication-panel agents score the protocol and protocol artefacts
  greater than 95/100, or bounded blockers are recorded.
- The protocol cites only repo-local artifacts or explicitly labelled external
  gates.
- A focused test validates required headings and referenced local paths.
- Repo-local verification passes with focused pytest, Ruff, example validation,
  and link/path checks added for the protocol.

## Out of Scope

- Writing the final full article, supplement, or journal-specific submission
  package.
- Claiming live source retrieval, journal acceptance, or external registry
  publication.
- Making new legal interpretations or certifying OIA outcomes.
