# Plan: Ontology and SHACL maturation

## Phase 1: Ontology Gap Audit [checkpoint: 1badee3]

- [x] Task: Audit ontology, vocabularies, SHACL shapes, and context (`321e252`)
    - [x] Review OWL/RDF classes, SKOS vocabularies, JSON-LD context, mappings, and docs.
    - [x] Identify missing provenance, authority, review, publication, and agent-boundary terms.
- [x] Task: Write RDF/SKOS parse and alignment tests (`c71cc97`)
    - [x] Validate ontology, vocab, and context parsing.
    - [x] Cover expected namespace bindings and core class/property presence.
- [x] Task: Implement ontology maturation baseline (`431f68e`)
    - [x] Add missing classes/properties and vocabulary entries.
    - [x] Document alignment with PROV-O, DCAT, ODRL, SKOS, and legal-document standards.
- [x] Task: Conductor - User Manual Verification 'Ontology Gap Audit' (Protocol in workflow.md) (`1badee3`)

## Phase 2: SHACL Safety Profiles [checkpoint: 100b968]

- [x] Task: Write SHACL validation tests (`95aa510`)
    - [x] Cover required evidence/provenance fields and certification-boundary constraints.
    - [x] Cover pySHACL installed and parse-only degraded modes.
- [x] Task: Implement SHACL profile updates (`f532c27`)
    - [x] Add shapes for request profiles, core events, agent actions, and publication metadata.
    - [x] Keep unsafe certification claims invalid or review-required.
- [x] Task: Conductor - User Manual Verification 'SHACL Safety Profiles' (Protocol in workflow.md) (`100b968`)

## Phase 3: Semantic Export Consistency [checkpoint: bf7b1ac]

- [x] Task: Write semantic export consistency tests (`ba6a63f`)
    - [x] Verify RDF export, JSON-LD context, dataset metadata, and graph export use consistent identifiers.
    - [x] Verify docs and examples stay aligned.
- [x] Task: Implement semantic export updates (`8bf62a4`)
    - [x] Align exporters and examples with matured ontology terms.
    - [x] Update docs with validation commands and expected outputs.
- [x] Task: Conductor - User Manual Verification 'Semantic Export Consistency' (Protocol in workflow.md) (`bf7b1ac`)

## Phase 4: Ontology Track Closeout

- [ ] Task: Run ontology validation
    - [ ] Run RDF, JSON-LD, SKOS, SHACL, schema, and export tests.
    - [ ] Run pySHACL path when dependency is installed or document external gate.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Ontology Track Closeout' (Protocol in workflow.md)
