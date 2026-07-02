# An agent-facing process ontology for New Zealand Official Information Act administration

## Abstract

FOI-O NZ is a schema-first process model, ontology, validation stack, and
analytical workbench for New Zealand Official Information Act administration.
It describes request profiles, observed correspondence events, review queues,
publication metadata, and bounded agent contracts in a form that can be checked
locally. The project is not legal advice and is not an official government publication.
Its design goal is process-support-only: authorised humans certify
release, refusal, redaction, charging, extension, transfer, complaint, and
publication outcomes.

## Motivation

Public OIA request records contain useful process signals, but they mix observed
events, inferred states, agency records, and platform-specific labels. FOI-O NZ
keeps those distinctions explicit by separating source-state preservation,
normalised state mapping, event provenance, human review, and publication
caveats. The current implementation status is maintained in
`docs/11-implementation-status.md`, while release-readiness proof is tracked in
`docs/19-release-readiness-evidence.md`.

## Architecture

The Python control plane owns JSON Schema validation, Pydantic models, FYI
manifest normalisation, event extraction, quality gates, reporting profiles,
RDF export, SHACL validation, publication metadata, and CLI commands. Optional
surfaces such as FastMCP, pySHACL, LanceDB, and Mojo/MAX add runtime capability
where installed, but deterministic Python and fixture-based paths remain the
repo-local compatibility proof.

Semantic alignment is recorded in `docs/22-semantic-alignment.md`. Publication
packaging is recorded in `docs/23-release-package.md`. The release checklist and
repository release metadata fixtures are `examples/release-checklist.v0.9.0.json`
and `examples/repository-release-metadata.v0.9.0.json`.

## Data Model

The core data model is organised around request profiles, process events,
agent actions, review tasks, ledgers, chunks, risk assessments, reporting
metrics, and publication metadata. The main event contract is
`schemas/json/core-event.schema.json`; semantic constraints are represented in
`shacl/foi-o-nz.shapes.ttl`.

Events carry assertion status, evidence references, generator metadata, and
human-certification metadata. Candidate events can be useful for routing and
review, but their status is not promoted to a final human outcome unless an
authorised human record supplies the certification evidence.

## Human Certification Boundary

The human boundary is intentionally redundant across schemas, quality gates,
agent policies, MCP/tool descriptors, SHACL shapes, examples, and tests. Agents
may map observed states, generate candidate process events, prepare summaries,
assemble review packs, and validate evidence. Authorised humans certify final
decisions and legally meaningful process outcomes.

The boundary is tested in release and publication checks, including
`tests/test_publication_metadata.py`, and is reflected in generated metadata
through explicit rights notices, external gates, and manual approval fields.

## Evaluation and Validation

Repo-local validation is the evidence base for implementation claims. The core
commands are:

- `uv run pytest -q`
- `uv run python scripts/validate_examples.py`
- `uv run foi-o-nz validate-repo`
- `uv run foi-o-nz schema-drift`

Additional release-package checks validate metadata fixtures, current repository
URLs, external-gate labels, and publication rights boundaries. Native Mojo/MAX
checks and live publication registries are treated as separate external gates
unless the relevant tooling, credentials, and human approval are present.

## Limitations

FOI-O NZ does not retrieve live source systems by default, host source request
payloads, publish registry deposits, replace agency records, decide statutory
interpretation, or provide legal advice. The repository can prove local
contracts, fixture workflows, and deterministic transformations; it cannot prove
live FYI/archive availability, registry acceptance, or operator approval.

Generated dataset and repository metadata keep source FYI/archive content rights
separate from the repository's MIT-licensed code, schemas, ontology, examples,
and documentation.

## Reproducibility

The release package records repeatable local evidence and external gates. A
maintainer can regenerate the release checklist and repository release metadata
with:

```bash
uv run foi-o-nz release-checklist --output examples/release-checklist.v0.9.0.json --release-version 0.9.0
uv run foi-o-nz repository-release-metadata docs/23-release-package.md examples/release-checklist.v0.9.0.json examples/dataset-metadata.examples.json docs/23-methods-paper.md --output examples/repository-release-metadata.v0.9.0.json --release-version 0.9.0 --base-dir .
```

The resulting package is ready for manual publication review when the repo-local
checks pass and every external registry or live-source gate is either completed
by an operator or explicitly recorded as still external.

## Publication Quality Review

Publication-facing outputs are reviewed through the panel defined in
`docs/29-publication-quality-panel.md`. The current baseline panel review for
this methods draft is `examples/publication-panel-review.methods-paper.json`,
and the initial MIRO checklist adherence report is
`examples/reporting-checklist-adherence.methods-paper-miro.json`.

The baseline review does not mark this draft as journal-ready. It records the
remaining work needed for the full protocol, results report, generated diagrams,
plots, tables, Cosmograph-compatible graph assets, manuscript, and supplement.
