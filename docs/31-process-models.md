# FOI-O NZ process model artefacts

FOI-O NZ has both an ontology and a process model.

The ontology is the semantic layer: `ontology/foi-o-nz.ttl`,
`vocab/*.skos.ttl`, `shacl/foi-o-nz.shapes.ttl`, JSON-LD context, RDF export,
and semantic-alignment tests. It defines classes, properties, controlled
vocabularies, provenance, publication metadata, and safety constraints.

The process model is the workflow layer: request states, event families,
transition guards, timelines, transition audits, and process diagrams. It
describes how a request may move through observable and candidate lifecycle
states while preserving the human-certification boundary.

## Process Model Formats

| Format | Path | Purpose | Boundary |
| --- | --- | --- | --- |
| Mermaid state machine | `examples/state-machine.mmd` | Lightweight documentation diagram. | Descriptive source for readers and docs. |
| BPMN 2.0 | `process_models/foi-o-nz-core.bpmn` | Process-analysis interchange model for the main OIA request workflow. | Review model only; it does not certify decisions. |
| PNML Petri net | `process_models/foi-o-nz-core.pnml` | Formal concurrency/reachability-friendly process model. | Abstract model only; final decision places still require human certification evidence. |
| Generated BPMN 2.0 | `process_models/foi-o-nz-state-machine.bpmn` | Canonical state-transition export generated from `src/foi_o_nz/state_machine.py`. | Regenerable state model, not an executable legal workflow. |
| Generated PNML Petri net | `process_models/foi-o-nz-state-machine.pnml` | Canonical Petri net export generated from `src/foi_o_nz/state_machine.py`. | Regenerable state model, not a legal decision system. |
| Generated Mermaid | `process_models/foi-o-nz-state-machine.mmd` | Canonical Mermaid export generated from `src/foi_o_nz/state_machine.py`. | Regenerable documentation source. |

## Model Scope

The BPMN and Petri net artefacts model the conservative NZ-first request
workflow represented by the current state machine and transition checks:

1. observe or receive a request;
2. validate or clarify scope;
3. route transfer, search, consultation, extension, or charge-assessment paths;
4. identify records or no records;
5. draft a decision pack;
6. require human certification before release, refusal, or partial release;
7. close, publish, or route complaint/review observations.

These models intentionally do not model other countries, official PSC returns,
agency-internal case-management details, or legal merits. They are companion
artefacts for ontology reporting, operations-research review, and future process
mining. They do not replace the ontology.

The process-mining fixture layer is documented in
`docs/32-process-mining-fixtures.md`. It provides XES and OCEL-style exports for
one committed release-path fixture only; it is not live corpus validation and
does not support agency performance, bottleneck, or cycle-time claims.

## Validation

The process-model source files are parsed and checked by
`tests/test_process_models.py`. The tests require:

- BPMN start/end events, tasks, gateways, and sequence flows;
- a human-certification task before decision communication;
- PNML places, transitions, arcs, and human-certification transition;
- alignment between documented process-model paths and committed files.
- byte-for-byte agreement between generated state-machine BPMN/PNML/Mermaid
  files and the generator in `src/foi_o_nz/process_models.py`.
- a conformance report at
  `examples/process-model-conformance.ontology-maturation.json` that records
  intentional abstraction differences between hand-authored workflow models and
  generated canonical state-transition exports.
