# FOI-O NZ ontology methods protocol

## Core/profile boundary

FOI-O is a global process-modelling method and conceptual frame for freedom of
information workflows. It originated with the NZ profile and has iterated
through Australian Commonwealth and NSW adapters. NZ remains the mature
reference implementation; Australian adapters are candidate-only until their
empirical and human-promotion evidence passes.

The original maturation stage was grounded in NZ evidence. The current method
keeps that provenance while applying the global core/profile contract to
Australian jurisdictions. It never treats country-specific terms, calendars,
law, reporting categories, or mappings as globally interchangeable.

## Objectives

The protocol defines how the repository develops the FOI-O NZ ontology,
schemas, vocabularies, SHACL shapes, mappings, validation checks, and
publication artefacts from repo-local evidence. The objectives are to:

- preserve public-source observations before interpretation;
- separate candidate process events from human-certified outcomes;
- keep ontology, schema, and agent-safety claims traceable to repo evidence;
- document what the current NZ profile can and cannot prove;
- prepare publication outputs without treating journal, registry, or live-source
  checks as completed repo-local proof.

## Materials

Protocol inputs are limited to committed repository artefacts and explicitly
labelled external gates. The primary repo-local materials are:

- `README.md`;
- `docs/00-repo-charter.md`;
- `docs/01-foundations-register.md`;
- `docs/02-system-architecture.md`;
- `docs/03-process-profile.md`;
- `docs/04-agent-boundaries.md`;
- `docs/06-legal-versioning.md`;
- `docs/07-evaluation-plan.md`;
- `docs/11-implementation-status.md`;
- `docs/19-release-readiness-evidence.md`;
- `docs/20-corpus-profile-goldset.md`;
- `docs/21-psc-reporting-profile.md`;
- `docs/22-semantic-alignment.md`;
- `ontology/foi-o-nz.ttl`;
- `shacl/foi-o-nz.shapes.ttl`;
- `vocab/request-states.skos.ttl`;
- `vocab/event-types.skos.ttl`;
- `vocab/assertion-status.skos.ttl`;
- `vocab/agent-boundaries.skos.ttl`;
- `schemas/json/`;
- `examples/`;
- `tests/`.

The companion inventory, claims, source, terminology, and coverage artefacts
are:

- `docs/24-ontology-methods-evidence-inventory.md`;
- `docs/24-ontology-claims-register.md`;
- `docs/24-ontology-source-register.md`;
- `docs/24-ontology-terminology-crosswalk.md`;
- `docs/24-schema-ontology-coverage-matrix.md`.

## Ontology Development Method

The method is schema-first and process-first.

1. Scope the domain from NZ OIA administration, public FYI/Alaveteli records,
   legislation/guidance references, PSC-style reporting needs, and agent-safety
   boundaries.
2. Preserve source labels, timestamps, identifiers, correspondence references,
   and provenance before normalising any state or event.
3. Encode operational contracts as JSON Schema and Pydantic models.
4. Define controlled vocabularies in SKOS for request states, event types,
   assertion status, and agent boundaries.
5. Add OWL/RDF classes and properties for request profiles, process events,
   evidence, human certification, review tasks, publication metadata, legal
   source versions, and provider runs.
6. Add SHACL shapes for semantic consistency and safety constraints, especially
   around human certification.
7. Validate examples, mappings, RDF/SHACL exports, publication metadata, and
   agent descriptors through repo-local tests.
8. Record unsupported, live-source, registry, journal, and human-approval items
   as external gates.

## Competency Questions

These questions define the minimum evaluation frame for the current NZ profile.

| ID | Competency question | Repo-local evidence | Current status |
| --- | --- | --- | --- |
| CQ1 | Can a request preserve its raw FYI/Alaveteli source state separately from a normalised state? | `schemas/json/request-profile.schema.json`, `examples/request-record.jsonld`, `tests/test_request_profile_jsonld.py` | Supported by fixtures. |
| CQ2 | Can a source state be mapped without treating the mapping as a final legal outcome? | `src/foi_o_nz/state_machine.py`, `docs/03-process-profile.md`, `tests/test_state_machine.py` | Supported by deterministic mapping tests. |
| CQ3 | Can candidate process events cite evidence and carry assertion status? | `schemas/json/core-event.schema.json`, `examples/core-event.extension-notified.json`, `tests/test_models.py` | Supported by schema and model tests. |
| CQ4 | Can decision-like events be blocked from autonomous machine certification? | `docs/04-agent-boundaries.md`, `src/foi_o_nz/agent_policy.py`, `shacl/foi-o-nz.shapes.ttl`, `tests/test_agent_policy.py`, `tests/test_shacl_safety_profiles.py` | Supported by policy and SHACL tests. |
| CQ5 | Can clock outputs warn when public-holiday evidence is missing or incomplete? | `docs/03-process-profile.md`, `examples/nz-public-holidays-2026.govt-nz.json`, `tests/test_dates.py` | Supported for fixture-mode warnings. |
| CQ6 | Can legal and guidance references retain source-version metadata? | `docs/06-legal-versioning.md`, `mappings/nz-legislation-sources.yaml`, `tests/test_legal_sources.py` | Supported by repo-local mapping validation. |
| CQ7 | Can PSC-style metrics be classified by public-data derivability rather than overclaimed as official reporting? | `docs/21-psc-reporting-profile.md`, `mappings/psc-oia-statistics-profile.yaml`, `examples/psc-report.small.json`, `tests/test_reporting.py` | Supported by sample reports and caveats. |
| CQ8 | Can public-data limitations and external gates be surfaced in release metadata? | `docs/19-release-readiness-evidence.md`, `examples/release-checklist.v0.9.0.json`, `examples/repository-release-metadata.v0.9.0.json`, `tests/test_release_package.py` | Supported by release-package tests. |
| CQ9 | Can publication assets carry captions, text alternatives, source inputs, commands, and provenance? | `schemas/json/generated-asset-manifest.schema.json`, `examples/generated-asset-manifest.foi-o-publication.json`, `docs/25-generated-asset-index.md` | Supported by manifest validation. |
| CQ10 | Can global FOI-O reuse be described without claiming cross-jurisdiction validation? | `README.md`, this protocol, `docs/24-ontology-claims-register.md` | Supported as a documentation boundary. |

## Empirical Evaluation Plan

The current empirical plan remains annotation-first. The machine-readable plan
is `examples/empirical-taskset-manifest.nz-first.json`, validated against
`schemas/json/empirical-taskset-manifest.schema.json`. Proposed task sets are:

| Task set | Target size | Purpose | Current evidentiary status |
| --- | ---:| --- | --- |
| State mapping | 100 requests | Review source-state to normalised-state mapping. | Defined as an annotation task set; not a completed gold standard until human reviewed. |
| Timeline extraction | 30 requests | Review received, acknowledgement, extension, transfer, decision, and release dates. | Planned annotation task set. |
| Outcome extraction | 30 requests | Review release, refusal, no-information, withdrawal, and partial outcomes. | Planned annotation task set. |
| Legal issue spotting | 20 decisions | Identify candidate withholding grounds and public-interest discussion. | Planned review-only task set; not legal certification. |
| Attachment profile | 20 attachments | Classify content type, record type, OCR need, and redaction presence. | Planned annotation task set. |

No task set becomes a gold standard until the reviewed records, reviewer
process, adjudication notes, and provenance are committed or otherwise recorded
as review evidence. Until then, these are annotation tasks.

## Validation

Repo-local validation for this protocol is bounded to deterministic commands and
committed fixtures:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
uv run foi-o-nz schema-drift
uv run pytest -q tests/test_ontology_maturation_plan.py
uv run pytest -q tests/test_semantic_alignment.py tests/test_rdf_export.py tests/test_shacl_safety_profiles.py
```

Full release-readiness validation additionally requires the full test suite,
Ruff check, Ruff format check, and available Mojo/Pixi checks or explicit
external-gate notes.

## Governance

Agents may prepare candidate events, review tasks, summaries, retrieval
contexts, redaction candidates, quality reports, publication metadata, and
annotation tasks. Agents must not certify access, refusal, redaction, charging,
extension, transfer, complaint, publication, or official reporting outcomes.

## Generated Assets

Publication assets are source artefacts, not decorative outputs. Each generated
or publication-facing asset must have:

- an asset id;
- a file path;
- an asset type;
- a caption;
- alt text or a textual equivalent;
- source inputs;
- a generation command or documented manual source;
- a provenance note;
- an intended manuscript or supplement location.

The current machine-readable manifest is
`examples/generated-asset-manifest.foi-o-publication.json`.

## Ontology and Process Model Boundary

The ontology and process model are distinct but aligned.

- The ontology defines semantic entities, vocabularies, provenance, publication
  metadata, and safety constraints.
- The process model defines lifecycle states, transitions, workflow diagrams,
  audit checks, and review-only process-analysis artefacts.

The current process-model sources are `examples/state-machine.mmd`,
`process_models/foi-o-nz-core.bpmn`, and `process_models/foi-o-nz-core.pnml`.
They support BPMN and Petri net review without erasing the NZ origin, silently
changing the global core, or claiming executable legal workflow status.

## Limitations

The protocol validates only the NZ profile and repo-local surfaces. It does not
prove live FYI/archive completeness, live legal-source freshness, official PSC
reporting, legal correctness, registry publication, journal acceptance, arXiv
upload, or cross-jurisdiction transferability.

## Reproducibility

The protocol is reproducible when the repo-local checks pass and every
referenced file exists. External gates must remain explicitly unresolved until
an operator supplies credentials, live-source snapshots, human review, or final
publication approval.

## Planned Analysis

The results track should report only what can be derived from committed
artefacts: inventory counts, validation coverage, schema/ontology alignment,
claim-support status, external-gate status, and generated-asset provenance.
Cross-jurisdiction comparison remains future work.
