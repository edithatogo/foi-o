# Contributing

FOI-O NZ is an ontology and process-modelling project. Contributions should preserve the distinction between source data, derived data, and human-certified administrative decisions.

## Contribution types

Useful contributions include:

- source mappings for OIA legislation, Ombudsman guidance, PSC statistics, and FYI/Alaveteli states;
- JSON Schema refinements;
- SHACL shapes;
- SKOS vocabulary entries;
- manually annotated examples from public FYI.org.nz records;
- tests for state transitions, extraction prompts, and agent safety boundaries;
- documentation improvements.

## Rules of the project

- Do not include private or unpublished OIA material.
- Do not paste large copyrighted source texts into the repo.
- Preserve source states and labels exactly; add normalised fields separately.
- Mark every extraction or mapping as observed, inferred, asserted, or certified.
- Do not describe an agent-generated legal conclusion as a decision.
- Include provenance wherever possible.

## Commit style

Suggested prefixes:

- `docs:` planning or documentation
- `schema:` JSON Schema or SHACL changes
- `vocab:` SKOS controlled vocabulary changes
- `ontology:` Turtle/OWL changes
- `mapping:` source or reporting mappings
- `test:` validation and examples
- `adr:` architecture decision records
