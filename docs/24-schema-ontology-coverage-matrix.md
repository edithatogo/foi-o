# FOI-O NZ schema/ontology coverage matrix

This matrix links the operational schema layer, semantic layer, examples, tests,
and agent-boundary rules. Counts are current for the repository state inspected
on 2026-07-15 and should be regenerated when the ontology or schema inventory
changes materially.

| Coverage area | Operational contract | Semantic surface | Example evidence | Test evidence | Boundary rule |
| --- | --- | --- | --- | --- | --- |
| Request profile | `schemas/json/request-profile.schema.json` | `foio:AccessRequest`, `foio:sourceState`, `foio:normalisedState` in `ontology/foi-o-nz.ttl`; `vocab/request-states.skos.ttl` | `examples/request-record.jsonld` | `tests/test_request_profile_jsonld.py`, `tests/test_models.py` | Source state is preserved separately from normalised state. |
| Core event | `schemas/json/core-event.schema.json` | `foio:ProcessEvent`, `foio:hasEvidence`, `foio:assertionStatus`; `vocab/event-types.skos.ttl` | `examples/core-event.extension-notified.json`, `examples/core-event.deadline-calculated.json` | `tests/test_event_extraction_timeline.py`, `tests/test_transitions.py` | Candidate events cite evidence and assertion status. |
| Human certification | `schemas/json/core-event.schema.json`, `schemas/json/agent-action.schema.json` | `foio:DecisionLikeEvent`, `foio:HumanCertification`, `foio:machineCertificationAllowed`; `foio:DecisionLikeEventShape` | `examples/agent-action.search-plan.json`, `examples/review-task.risk.json` | `tests/test_agent_policy.py`, `tests/test_shacl_safety_profiles.py` | Agents cannot certify decision-like outcomes. |
| Legal source versioning | `schemas/json/process-advice.schema.json`, mapping YAML | `foio:LegalSourceVersion`, `foio:sourceVersionId` | `mappings/nz-legislation-sources.yaml` | `tests/test_legal_sources.py` | Live source refresh is an external gate. |
| PSC reporting | `schemas/json/reporting-metric.schema.json`, `schemas/json/psc-report.schema.json` | `foio:ReportingMetric` | `examples/reporting-metric.completed-requests.json`, `examples/psc-report.small.json` | `tests/test_reporting.py`, `tests/test_reporting_docs.py` | Public-data derivability is not official reporting. |
| Publication metadata | `schemas/json/release-checklist.schema.json`, `schemas/json/repository-release-metadata.schema.json` | `foio:DatasetPublication`, `foio:PermissionPolicy`, `foio:publicationCaveat` | `examples/release-checklist.v0.9.0.json`, `examples/repository-release-metadata.v0.9.0.json` | `tests/test_release_package.py`, `tests/test_publication_metadata.py` | Registry and publication approval remain human/external gates. |
| Generated assets | `schemas/json/generated-asset-manifest.schema.json`, `schemas/json/graph-export.schema.json`, `schemas/json/process-mining-ocel.schema.json`, `schemas/json/process-mining-conformance.schema.json`, `schemas/json/empirical-taskset-manifest.schema.json` | Graph node properties include semantic URI hints. | `examples/generated-asset-manifest.foi-o-publication.json`, `examples/graph-export.foi-o-evidence-network.json`, `examples/process-mining.fixture.ocel.json`, `examples/process-mining-conformance.fixture.json`, `examples/empirical-taskset-manifest.nz-first.json` | `tests/test_ontology_maturation_plan.py`, `tests/test_process_mining.py`, `tests/test_empirical_taskset_manifest.py` | Assets must include caption, text alternative, source inputs, command, and provenance. |

## Inventory Snapshot

| Artefact class | Count |
| --- | ---:|
| JSON Schema files | 64 |
| Example files | 118 |
| Documentation files | 52 |
| OWL ontology files | 1 |
| SHACL files | 1 |
| SKOS vocabulary files | 4 |
| Mapping files | 3 |
| Python test modules | 54 |

## Semantic Snapshot

| File | Key coverage |
| --- | --- |
| `ontology/foi-o-nz.ttl` | 21 OWL classes, 9 object properties, and 17 datatype properties. |
| `shacl/foi-o-nz.shapes.ttl` | 6 node shapes. |
| `vocab/request-states.skos.ttl` | 17 SKOS concepts. |
| `vocab/event-types.skos.ttl` | 15 SKOS concepts. |
| `vocab/assertion-status.skos.ttl` | 5 SKOS concepts. |
| `vocab/agent-boundaries.skos.ttl` | 3 SKOS concepts. |
