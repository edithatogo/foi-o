# Foundations register

This register records the New Zealand sources that shaped FOI-O's first
jurisdiction profile. It documents the model's origin and NZ reference profile;
it does not make New Zealand the default for the global core or for other
jurisdictions.

## New Zealand legal and process sources

| ID | Source | Type | Why it matters | Machine-readable use |
|---|---|---|---|---|
| `nz.oia.act` | Official Information Act 1982 | Statute | Defines the central-government official-information regime, including purposes, eligibility, timeframes, transfers, decisions, withholding grounds, forms of access, and Ombudsman complaints. | Link events and rules to provision URLs and legislation API identifiers. |
| `nz.lgoima.act` | Local Government Official Information and Meetings Act 1987 | Statute | Deferred second regime. Useful to test whether the model separates central-government OIA concepts from local-government concepts. | Add after OIA core stabilises. |
| `nz.legislation.api` | New Zealand Legislation API v0 | API | Provides programmatic access to legislation using works, versions, and formats. | Store `work_id`, `version_id`, format URL, and retrieval timestamp for law references. |
| `nz.ombudsman.oia-guide` | The OIA for Ministers and agencies | Guidance | Best source for process model: requests, clarification, transfer, timeframes, consultation, extension, decision, release, charging, and complaints. | Convert headings and checklists into process events and quality gates. |
| `nz.ombudsman.guides-index` | Ombudsman OIA guides and resources | Guidance index | Section-specific guidance on charging, delay, consultation, legal privilege, public interest, substantial collation, and refusal grounds. | Seed issue-spotting categories and controlled vocabularies. |
| `nz.psc.oia-statistics` | Public Service Commission OIA statistics | Reporting dataset | Defines national reporting categories: completed requests, timeliness, publication, complaints, extensions, transfers, refusals, response times. | Create reporting metric profiles and aggregate outputs. |
| `nz.ombudsman.complaints-data` | Ombudsman OIA/LGOIMA complaints data | Reporting dataset | Captures complaint volume, type, complainant type, completed complaint outcomes, and agency context. | Seed complaint/review event and outcome vocabulary. |
| `nz.public-service-ai-framework` | Public Service AI Framework | AI governance | Defines public-sector AI expectations: lawful, safe, responsible, human-centred, transparent, accountable. | Non-functional requirements and agent safety constraints. |
| `nz.algorithm-charter` | Algorithm Charter for Aotearoa New Zealand | Algorithm governance | Useful for transparency, human oversight, impact assessment, bias, and challenge pathways. | Align model cards and agent logs. |

## Existing project sources

| ID | Source | Role in this project |
|---|---|---|
| `repo.fyi-cli` | `edithatogo/fyi-cli` | Tool/client layer. Potential future exporter of FOI-O NZ events and local MCP server. |
| `repo.fyi-archive` | `edithatogo/fyi-archive` | Archive orchestration and publication layer. Provides manifests and provenance, but should not own the ontology. |
| `hf.fyi-archive-nz` | `edithatogo/fyi-archive-nz` | Initial public corpus for state mapping, attachment profiling, and extraction evaluation. |
| `platform.alaveteli` | Alaveteli | Upstream request-platform semantics and state labels. |

## Technical standards to reuse

| Standard | Role |
|---|---|
| JSON Schema | Validation for process events, agent actions, request records, and reporting metrics. |
| JSON-LD | Agent/API-friendly linked-data serialisation. |
| RDF/OWL | Formal ontology layer. |
| SHACL | Constraint validation over RDF graphs. |
| SKOS | Controlled vocabularies: states, outcomes, event types, assertion status, legal issues. |
| PROV-O | Provenance model for events, artefacts, derivations, agents, and activities. |
| DCAT | Future description of released datasets, disclosure logs, and published records. |
| ODRL | Future modelling of access/reuse permissions, constraints, and duties. |
| Akoma Ntoso / LegalDocML | Future statutory-document representation and provision-level linking. |
| MCP | Future agent-facing tool/resource/prompt surface, with strict safety contracts. |
