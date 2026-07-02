# Plan: Ontology and SHACL maturation

## Phase 1: Ontology Gap Audit

- [x] Task: Audit ontology, vocabularies, SHACL shapes, and context (`321e252`)
    - [x] Review OWL/RDF classes, SKOS vocabularies, JSON-LD context, mappings, and docs.
    - [x] Identify missing provenance, authority, review, publication, and agent-boundary terms.
- [x] Task: Write RDF/SKOS parse and alignment tests (`c71cc97`)
    - [x] Validate ontology, vocab, and context parsing.
    - [x] Cover expected namespace bindings and core class/property presence.
- [~] Task: Implement ontology maturation baseline
    - [ ] Add missing classes/properties and vocabulary entries.
    - [ ] Document alignment with PROV-O, DCAT, ODRL, SKOS, and legal-document standards.
- [ ] Task: Conductor - User Manual Verification 'Ontology Gap Audit' (Protocol in workflow.md)

## Phase 2: SHACL Safety Profiles

- [ ] Task: Write SHACL validation tests
    - [ ] Cover required evidence/provenance fields and certification-boundary constraints.
    - [ ] Cover pySHACL installed and parse-only degraded modes.
- [ ] Task: Implement SHACL profile updates
    - [ ] Add shapes for request profiles, core events, agent actions, and publication metadata.
    - [ ] Keep unsafe certification claims invalid or review-required.
- [ ] Task: Conductor - User Manual Verification 'SHACL Safety Profiles' (Protocol in workflow.md)

## Phase 3: Semantic Export Consistency

- [ ] Task: Write semantic export consistency tests
    - [ ] Verify RDF export, JSON-LD context, dataset metadata, and graph export use consistent identifiers.
    - [ ] Verify docs and examples stay aligned.
- [ ] Task: Implement semantic export updates
    - [ ] Align exporters and examples with matured ontology terms.
    - [ ] Update docs with validation commands and expected outputs.
- [ ] Task: Conductor - User Manual Verification 'Semantic Export Consistency' (Protocol in workflow.md)

## Phase 4: Ontology Track Closeout

- [ ] Task: Run ontology validation
    - [ ] Run RDF, JSON-LD, SKOS, SHACL, schema, and export tests.
    - [ ] Run pySHACL path when dependency is installed or document external gate.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Ontology Track Closeout' (Protocol in workflow.md)
