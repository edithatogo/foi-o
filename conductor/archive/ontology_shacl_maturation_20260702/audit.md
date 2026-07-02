# Ontology, SKOS, SHACL, and Context Audit

Date: 2026-07-02

## Reviewed Surfaces

- `ontology/foi-o-nz.ttl`
- `shacl/foi-o-nz.shapes.ttl`
- `vocab/*.skos.ttl`
- `contexts/foi-o-nz.context.jsonld`
- `src/foi_o_nz/jsonld_context.py`
- `src/foi_o_nz/rdf_export.py`
- `src/foi_o_nz/shacl_validation.py`
- `src/foi_o_nz/dataset_metadata.py`
- `src/foi_o_nz/graph_export.py`
- `docs/01-foundations-register.md`
- `docs/06-legal-versioning.md`

## Current Strengths

- The seed ontology already separates access requests, process events, decision-like events, human certification, agent actions, evidence, source records, attachments, legal references, reporting metrics, and agencies.
- The RDF exporter binds FOIO, DCTERMS, and PROV and can emit request/event graphs.
- The SHACL wrapper supports full pySHACL validation when installed and parse-only degraded mode otherwise.
- SKOS vocabularies exist for request states, event types, assertion status, and agent boundaries.
- Dataset metadata writers already use schema.org/Croissant-style JSON-LD and preserve caveats about non-certification.

## Gaps

1. Namespace and identifier drift
   - Most semantic files use `https://w3id.org/foio-nz/...`, while `contexts/foi-o-nz.context.jsonld` uses `https://w3id.org/foi-o-nz/ontology#`.
   - Tests should fail if FOIO namespace bindings diverge between ontology, JSON-LD context, RDF export, and metadata exports.

2. Ontology coverage gaps
   - Missing explicit classes for review tasks, risk assessments, redaction candidates, chunks, dataset/publication packages, disclosure logs, model/provider runs, and legal/guidance source versions.
   - Missing properties for source-system identifiers, source URLs, content hashes, review requirements, generated-output exclusion, legal effect, machine-certification allowance, publication caveats, and dataset distribution links.

3. Standards alignment gaps
   - PROV-O is present, but DCAT distribution/catalog concepts, ODRL policy/permission/prohibition/duty concepts, SKOS concept-scheme links, and legal-document/source-version terms are not yet represented in the ontology.
   - LegalDocML/Akoma Ntoso alignment should stay documentary and identifier-focused until statute-source retrieval is live.

4. SHACL safety gaps
   - Current shapes only target `ProcessEvent` and `DecisionLikeEvent`.
   - Shapes do not yet cover request-profile derivation, evidence/source provenance, agent-action safety, review-task routing, publication metadata caveats, or machine-certification prohibitions.
   - Decision-like event shape requires a human certification record for all targeted events; the JSON model allows candidate decision-like events with negative certification metadata. Shapes need to distinguish candidate/review-required records from positive human certification.

5. Export consistency gaps
   - RDF export uses literals for `eventType`, `assertionStatus`, and lifecycle state instead of SKOS concept URIs.
   - JSON-LD context does not expose newer fields such as `human_review_required`, `legal_effect`, `machine_certification_allowed`, `generated_output_included`, legal-source version fields, or publication metadata terms.
   - Graph and dataset metadata exports do not advertise their FOIO/DCAT/ODRL alignment consistently.

## Phase Recommendations

- Phase 1 should add parse/alignment tests that lock namespace consistency, required classes/properties, SKOS concept schemes, and JSON-LD context terms.
- Phase 1 implementation should mature the ontology/context baseline without changing exporter behavior too broadly.
- Phase 2 should expand SHACL profiles around evidence/provenance, agent-action safety, review-required candidate records, and publication caveats.
- Phase 3 should align RDF/JSON-LD/metadata/graph exporters with the matured ontology terms and add fixture-level consistency checks.
- Live legal-source retrieval and external registry validation remain external gates; this track should only commit repo-local source-version identifiers and validation paths.
