# Semantic Alignment Notes

FOI-O NZ uses a small repo-local semantic layer to keep request/process data,
agent boundaries, and publication metadata aligned without claiming full legal
automation.

## Canonical namespaces

- FOI-O NZ ontology: `https://w3id.org/foio-nz/ontology#`
- FOI-O NZ request IDs: `https://w3id.org/foio-nz/request/`
- FOI-O NZ event IDs: `https://w3id.org/foio-nz/event/`

The JSON-LD context, RDF exporter, ontology, and dataset metadata should use the
same FOI-O namespace unless a later migration is explicitly versioned.

## Standards alignment

- **PROV-O**: process events, provider runs, review tasks, and evidence artefacts
  use provenance classes and derivation relationships.
- **SKOS**: request states, event types, assertion status, and agent boundaries
  remain controlled vocabularies rather than unrestricted strings.
- **DCAT**: dataset publications and disclosure-log style packages are modelled
  as publication/catalogue artefacts with distributions.
- **ODRL**: publication and reuse constraints are represented as policy
  references before any richer licence or permission modelling is attempted.
- **Legal-document standards**: statute and guidance alignment is identifier-led
  through `LegalSourceVersion` until live source retrieval and provision-level
  parsing are implemented as explicit external gates.

## Boundary

Semantic alignment does not certify release, refusal, redaction, charging,
extension, transfer, complaint, or publication outcomes. It records provenance,
review requirements, legal-source identifiers, and publication caveats so humans
can inspect the evidence trail.
