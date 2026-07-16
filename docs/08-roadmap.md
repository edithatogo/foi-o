# Roadmap

## Phase 0 — Repo foundations

- Standalone repo created.
- Project charter, ADRs, safety stance, and source register added.
- JSON Schemas, RDF, SHACL, SKOS, mappings, and examples pass syntax checks.

## Phase 1 — Corpus profile

- Load `fyi-archive-nz` manifest fields.
- Preserve source state and add normalised state mapping.
- Define request-level JSON-LD profile.
- Build sample gold set for state mapping.

## Phase 2 — Event extraction

- Extract observed events from public correspondence.
- Add timeline reconstruction.
- Distinguish observed, inferred, asserted, and certified claims.
- Add confidence and provenance fields.

## Phase 3 — OIA process rules

- Add indicative statutory clock calculation.
- Map OIA/Ombudsman guidance to quality gates.
- Add source-versioned statutory/guidance references.

## Phase 4 — Reporting profile

- Map FOI-O NZ event logs to PSC reporting categories.
- Identify what FYI public data can and cannot support.
- Produce sample aggregate reports.

## Phase 5 — Agent contract

- Define safe MCP resources/tools/prompts.
- Add conformance tests for tool descriptors.
- Implement read-only prototype server over sample data.

## Phase 6 — Ontology maturation

- Expand OWL classes and properties.
- Add SHACL validation profiles.
- Align with PROV-O, DCAT, ODRL, SKOS, and legal-document standards.
- Publish versioned releases.

## Phase 7 — Empirical V2 contract and publication loop

- Preserve V1 provenance, epistemic-status, and human-certification guarantees.
- Require immutable source/profile/model pins and machine-readable capability
  declarations for each extraction adapter.
- Evaluate against rights-reviewed heldout data with independent annotation,
  adjudication, per-capability metrics, and regression thresholds.
- Feed accepted contracts into `fyi-archive` re-extraction and versioned Hugging
  Face/Zenodo publication; retain failed and superseded evaluations as evidence.
- Promote no adapter or ontology mapping without explicit human approval.

## Phase 8 — Australian jurisdiction profiles

- Maintain one versioned core (`foi-o`) and independently versioned country and
  subdivision profiles (`foi-o-au`, `foi-o-au-nsw`, and peers), not long-lived
  jurisdiction branches.
- Pilot Commonwealth and NSW mappings first using legislation source packs and
  jurisdiction-specific examples.
- Keep all pilots candidate-only until source, rights, annotation, evaluation,
  compatibility, and human legal-review gates pass.
- Add the remaining states and territories incrementally; do not infer their
  clocks, review pathways, or legal concepts from Commonwealth or NSW fixtures.
- Publish compatibility manifests and migrations independently for the core,
  country profile, and each subdivision profile.
