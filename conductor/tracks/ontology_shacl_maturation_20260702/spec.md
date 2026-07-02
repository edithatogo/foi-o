# Specification: Ontology and SHACL maturation

## Objective

Expand OWL/SKOS/SHACL, enable pySHACL runtime validation, and align with PROV-O, DCAT, ODRL, SKOS, and legal-document standards.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/18
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Mature ontology classes/properties for requests, events, evidence, provenance, authority, review, publication, and agent boundaries.
- Expand SHACL validation profiles for required safety and provenance constraints.
- Align vocabulary use with PROV-O, DCAT, ODRL, SKOS, and legal-document standards where practical.
- Support pySHACL runtime validation when installed and parse-only/degraded validation when absent.

## Acceptance Criteria

- RDF, JSON-LD, SKOS, and SHACL artifacts parse and validate in fixture mode.
- pySHACL runtime path is tested when dependency is available, with explicit degraded-mode behavior otherwise.
- Ontology docs explain alignment decisions and non-goals.
- Certification-boundary constraints are represented in both schemas and SHACL profiles.
