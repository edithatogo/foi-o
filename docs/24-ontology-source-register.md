# FOI-O NZ ontology source register

This register records the source classes used in the protocol and whether they
support claims, background context, legal provenance, or formatting only.

| Source id | Source | Type | Use | Retrieval/status |
| --- | --- | --- | --- | --- |
| repo.charter | `docs/00-repo-charter.md` | Repo document | Scope, mission, non-goals. | Repo-local. |
| repo.foundations | `docs/01-foundations-register.md` | Repo document | NZ source categories and standards. | Repo-local. |
| repo.process-profile | `docs/03-process-profile.md` | Repo document | Process states, event families, epistemic status, certification. | Repo-local. |
| repo.agent-boundaries | `docs/04-agent-boundaries.md` | Repo document | Agent safety and prohibited autonomous actions. | Repo-local. |
| repo.legal-versioning | `docs/06-legal-versioning.md` | Repo document | Source-versioning method. | Repo-local. |
| repo.evaluation | `docs/07-evaluation-plan.md` | Repo document | Planned annotation/goldset task sizes and metrics. | Repo-local. |
| repo.release-evidence | `docs/19-release-readiness-evidence.md` | Repo document | Validation commands and external gates. | Repo-local. |
| repo.semantic-alignment | `docs/22-semantic-alignment.md` | Repo document | PROV-O, SKOS, DCAT, ODRL, and legal-source alignment. | Repo-local. |
| nz.oia.act | Official Information Act 1982 | Statute | Legal provenance and NZ context. | External source; version captured through `mappings/nz-legislation-sources.yaml` when refreshed. |
| nz.ombudsman.guidance | Ombudsman OIA guides and resources | Guidance | Background and process-source context. | External source; live freshness is external. |
| nz.psc.oia-statistics | Public Service Commission OIA statistics | Reporting source | Reporting profile context and derivability limits. | External source; official reporting remains external. |
| platform.alaveteli | FYI/Alaveteli source labels | Platform semantics | Source-state preservation and mapping. | Repo-local fixtures only unless live snapshot supplied. |
| journal.instructions | Journal and arXiv instructions | Publication formatting | Formatting and upload-readiness only. | Must be refreshed during submission track. |

## Source-Use Rules

- Repo-local documents can support claims about repository design and validation.
- External legal/guidance/reporting sources can support source provenance and
  background only when retrieval/version details are recorded.
- Journal and arXiv sources support formatting and submission-readiness
  requirements only; they do not validate the ontology.
- No non-NZ source should be added during this maturation stage.
