# Repository charter

## Mission

FOI-O NZ defines a machine-readable, auditable model of New Zealand OIA process data for use by humans, software systems, and bounded AI agents.

## Non-goals

This repository does not:

- decide whether information should be released or withheld;
- replace OIA decision-makers;
- scrape or archive FYI.org.nz;
- host the archive payload;
- provide legal advice to requesters or agencies;
- become a public social interface for agents.

## Project boundaries

The initial repo should own:

- FOI-O NZ terminology;
- process events and state machine;
- JSON Schemas;
- RDF/OWL ontology seed;
- SKOS vocabularies;
- SHACL shapes;
- mappings to FYI/Alaveteli states and PSC reporting metrics;
- extraction/evaluation prompts;
- example records;
- agent safety contracts.

The repo should depend on, rather than absorb, existing projects:

- `fyi-cli` for capture, active archive orchestration, and request-management tools (succeeding `fyi-archive`);
- `fyi-archive` as historical archive repository and reference provenance;
- `fyi-archive-nz` for the public corpus;
- NZ Legislation API / legislation.govt.nz for statutes;
- Ombudsman and PSC resources for guidance and reporting definitions.
