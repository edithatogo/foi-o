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
