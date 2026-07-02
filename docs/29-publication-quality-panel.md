# Publication quality panel

This panel is the review framework for FOI-O NZ publication outputs. It is an
advisory quality gate, not a replacement for journal peer review, legal review,
publisher checks, or human author approval.

## Artifacts reviewed

- protocol;
- analysis/results;
- generated artefacts, including diagrams, plots, tables, Cosmograph-compatible
  graph data, and asset manifests;
- report, discussion, and conclusion;
- manuscript;
- supplement;
- release package.

## Required agents

| Agent ID | Role | Primary review focus |
|---|---|---|
| `editor` | Editor | Argument, structure, audience fit, and article coherence. |
| `peer_reviewer` | Peer reviewer | Methods, evidence, reproducibility, and scholarly contribution. |
| `copy_editor` | Copy editor | Clarity, grammar, consistency, and publication-ready prose. |
| `publisher` | Publisher/production editor | Submission package completeness, declarations, files, and production risks. |
| `ontology_expert` | Ontology/semantic-web expert | OWL/RDF/SKOS/SHACL modelling, namespace consistency, and ontology reporting. |
| `public_admin_expert` | OIA/public-administration expert | Public-sector process fit, OIA boundaries, and governance caveats. |
| `legal_informatics_expert` | Legal-informatics/source-provenance expert | Legal/guidance source provenance, non-legal-advice boundary, and identifier quality. |
| `economist` | Economist | Claims about public value, reporting indicators, cost/time implications, and non-derivable metrics. |
| `operations_researcher` | Operations researcher/process-modelling expert | State/event process logic, queues, bottlenecks, and workflow validity. |
| `reproducibility_expert` | Data-engineering/reproducibility expert | Deterministic commands, fixtures, schemas, provenance, and rebuildability. |
| `visualization_expert` | Visualization/network-analysis expert | Diagrams, plots, tables, graph data, Cosmograph suitability, captions, and accessibility. |
| `red_team` | Red-team agent | Overclaiming, unsafe automation, misleading legal/reporting claims, and failure modes. |
| `devils_advocate` | Devil's-advocate agent | Alternative interpretations, weak assumptions, missing counterarguments, and scope creep. |

## Scoring rule

Each required agent scores each applicable artifact out of 100. An artifact is
not publication-ready until every required score is greater than 95/100 or a
bounded blocker records why the threshold cannot be reached without an external
decision.

Scores must use the contracts in:

- `schemas/json/publication-panel-scorecard.schema.json`
- `schemas/json/publication-panel-review.schema.json`

## Improvement loop

1. Run the panel review for the artifact.
2. Record machine-readable scorecards and concise findings.
3. Apply high-confidence fixes that do not exceed the artifact scope.
4. Rerun the panel review.
5. Continue until every required score is greater than 95/100 or a bounded
   blocker is recorded.

## Reporting and checklist contracts

Checklist sources and adherence reports use:

- `schemas/json/reporting-checklist-source.schema.json`
- `schemas/json/reporting-checklist-adherence.schema.json`

Initial relevant checklist sources are:

- MIRO, for ontology reporting completeness.
- FAIR principles, for data/software metadata and reuse.
- MDAR-style transparency checks, used only as a broad reporting-transparency
  reference unless the selected journal requires it.

Journal-specific checklists must be refreshed during the journal submission
track and recorded with source URL, retrieval date, applicability, and evidence
paths.

## Current baseline review

The current methods paper has been reviewed as a baseline artifact in
`examples/publication-panel-review.methods-paper.json`. It is useful as an
early methods summary, but it is not yet ready for journal submission because it
does not include the full protocol, results report, generated visual assets,
supplement, selected journal requirements, or checklist adherence package.
