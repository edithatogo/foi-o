# FOI-O NZ

**FOI-O NZ** is a New Zealand-first, agent-facing process model for Official Information Act administration.

The project is not a chatbot and not a decision engine. Its purpose is to define the machine-readable substrate that lets bounded agents and human officials interact safely with OIA process data: requests, correspondence, statutory clocks, search plans, evidence, states, release/refusal events, reviews, reporting metrics, and provenance.

## Why this repo exists

This repo is deliberately separate from the existing FYI tooling stack:

| Repository / dataset | Role | Relationship to FOI-O NZ |
|---|---|---|
| `edithatogo/fyi-cli` | Capture and request-management client for FYI.org.nz / Alaveteli-style request systems. | A source/tool client. It may later expose FOI-O NZ events or run validation locally. |
| `edithatogo/fyi-archive` | Archive orchestration, manifests, mirror verification, provenance, Hugging Face/Zenodo/OSF publishing. | A corpus substrate. It should not own legal/process ontology design. |
| `edithatogo/fyi-archive-nz` | Public Hugging Face dataset of FYI.org.nz request records. | The initial public corpus for empirical state mapping and extraction tasks. |
| `foi-o-nz` | Process profile, ontology, vocabularies, SHACL, JSON Schemas, agent contracts, evaluation harness. | The semantic and agent-facing layer. |

## Core design choices

1. **NZ-first, not world-first.** Start with the OIA and FYI.org.nz because they provide a bounded legal regime and a public archive.
2. **Process profile before full ontology.** First define events, states, evidence, and validation rules; then formalise them into RDF/OWL/SHACL.
3. **Observed ≠ inferred ≠ certified.** The model must distinguish source facts from agent inferences and human-certified administrative decisions.
4. **Agents guide process; humans make legal decisions.** Agents can triage, extract, validate, calculate, draft, and quality-check. They must not autonomously grant, refuse, redact, charge, transfer, extend, or determine complaints.
5. **Provenance is not optional.** Every derived claim should point to a source artefact, extraction method, timestamp, and confidence level.
6. **Legal versioning matters.** A historical request should be interpreted against the law, guidance, and agency context applicable at the relevant time.

## Repository map

```text
foi-o-nz/
├── adr/                         # Architecture decision records
├── docs/                        # Planning, governance, architecture, roadmap
├── examples/                    # Example JSON-LD/events/agent actions/state machine
├── mappings/                    # Alaveteli, PSC, legislation, and reporting mappings
├── ontology/                    # OWL/RDF/Turtle ontology seed
├── prompts/                     # Structured extraction/evaluation prompts
├── schemas/json/                # JSON Schemas for events, requests, agent actions, metrics
├── shacl/                       # SHACL validation shapes
├── tests/                       # Syntax and sample validation tests
├── vocab/                       # SKOS controlled vocabularies
├── .github/workflows/validate.yml
├── Makefile
└── pyproject.toml
```

## Suggested first milestone

The first milestone should not be “complete ontology”. It should be:

> **Milestone 0.1: an auditable OIA process event model for public FYI.org.nz request records.**

Acceptance criteria:

- Source FYI/Alaveteli states are preserved exactly.
- Normalised FOI-O NZ states are mapped separately with confidence and method.
- Events have evidence references and assertion status.
- Decision-like events require human certification fields.
- JSON Schemas, RDF/Turtle, SHACL, YAML mappings, and examples pass CI syntax checks.
- A small, manually-reviewed gold set exists for state mapping and event extraction.

## Validation

```bash
uv sync --extra dev
uv run pytest
make validate
```

The validation suite is intentionally lightweight at this stage. It checks JSON Schema syntax, example conformance, YAML syntax, and RDF/SHACL parseability.

## Naming note

The repo name uses “FOI” because the broader international field is commonly called freedom of information / access to information. The initial domain model is New Zealand OIA-specific. The ontology namespace uses `foio-nz` to avoid pretending that the initial profile is jurisdiction-neutral.
