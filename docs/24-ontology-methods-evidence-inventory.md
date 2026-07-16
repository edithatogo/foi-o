# FOI-O NZ ontology methods evidence inventory

This inventory is the source list for the methods protocol. It separates
repo-local evidence from external gates and avoids adding non-NZ jurisdictional
material at this stage.

| Evidence class | Representative paths | Use in method | Status |
| --- | --- | --- | --- |
| Charter and scope | `docs/00-repo-charter.md`, `README.md`, ADRs in `adr/` | Defines mission, non-goals, standalone-repo rationale, and human-certification boundaries. | Repo-local. |
| Foundations | `docs/01-foundations-register.md`, `mappings/nz-legislation-sources.yaml` | Defines the NZ-origin legal, guidance, reporting, platform, and technical source categories used to bootstrap the global model. | Repo-local NZ reference register; Australian source packs are independently versioned and gated. |
| Architecture | `docs/02-system-architecture.md`, `docs/assets/foi-o-process-architecture.mmd` | Describes source, archive, semantic, agent, reporting, and evaluation layers. | Repo-local. |
| Process profile | `docs/03-process-profile.md`, `vocab/request-states.skos.ttl`, `vocab/event-types.skos.ttl` | Defines lifecycle states, event families, assertion status, and certification boundary. | Repo-local. |
| Agent safety | `docs/04-agent-boundaries.md`, `src/foi_o_nz/agent_policy.py`, `schemas/json/agent-action.schema.json` | Defines safe, human-certified, risky, and prohibited autonomous actions. | Repo-local. |
| Legal versioning | `docs/06-legal-versioning.md`, `src/foi_o_nz/legal_sources.py`, `tests/test_legal_sources.py` | Records source-version metadata and fails closed around live retrieval. | Repo-local; live retrieval external. |
| Evaluation | `docs/07-evaluation-plan.md`, `docs/20-corpus-profile-goldset.md`, `schemas/json/goldset-task.schema.json` | Defines annotation task sets and metrics before scale-up. | Planned task sets; fixture tests exist. |
| Schemas and models | `schemas/json/`, `src/foi_o_nz/models.py` | Defines operational data contracts before semantic enrichment. | Repo-local. |
| Ontology and vocabularies | `ontology/foi-o-nz.ttl`, `vocab/*.skos.ttl` | Defines OWL/RDF classes, properties, and controlled vocabularies. | Repo-local. |
| SHACL constraints | `shacl/foi-o-nz.shapes.ttl`, `tests/test_shacl_safety_profiles.py` | Validates semantic safety profiles and human-certification constraints. | Repo-local. |
| Examples | `examples/` | Provides small deterministic fixtures for schemas, validation, release, and publication. | Repo-local fixtures. |
| Release readiness | `docs/19-release-readiness-evidence.md`, `examples/release-checklist.v0.9.0.json` | Defines repeatable local validation and external gates. | Repo-local. |
| Reporting profile | `docs/21-psc-reporting-profile.md`, `mappings/psc-oia-statistics-profile.yaml`, `examples/psc-report.small.json` | Separates public-data indicators from official PSC reporting. | Repo-local sample; official reporting external. |
| Semantic alignment | `docs/22-semantic-alignment.md`, `tests/test_semantic_alignment.py` | Aligns FOI-O terms with PROV-O, SKOS, DCAT, ODRL, and legal-source references. | Repo-local. |
| Publication package | `docs/23-methods-paper.md`, `docs/26-journal-target-requirements.md`, `docs/27-submission-manuscript.md`, `docs/28-submission-supplement.md`, `docs/30-arxiv-readiness.md` | Provides manuscript and supplement source material with explicit human gates. | Repo-local drafts; live submission external. |
| Generated assets | `docs/25-generated-asset-index.md`, `examples/generated-asset-manifest.foi-o-publication.json`, `examples/graph-export.foi-o-evidence-network.json` | Provides diagrams, tables, graph data, captions, text alternatives, commands, and provenance. | Repo-local source assets. |

## External Gates

- Live FYI/archive pulls.
- Live NZ Legislation, Ombudsman, or PSC source refresh.
- Human-reviewed gold-standard completion.
- Official legal, Ombudsman, or PSC endorsement.
- Registry, dataset, journal, or arXiv publication.
- Final author, funding, conflicts, acknowledgements, and upload approval.
