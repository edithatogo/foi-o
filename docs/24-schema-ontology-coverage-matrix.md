# FOI-O NZ schema/ontology coverage matrix

This matrix links the operational schema layer, semantic layer, examples, tests,
and agent-boundary rules. Counts are current for the repository state inspected
on 2026-07-16 and should be regenerated when the ontology or schema inventory
changes materially.

| Coverage area | Operational contract | Semantic surface | Example evidence | Test evidence | Boundary rule |
| --- | --- | --- | --- | --- | --- |
| Request profile | `schemas/json/request-profile.schema.json` | `foio:AccessRequest`, `foio:sourceState`, `foio:normalisedState` in `ontology/foi-o-nz.ttl`; `vocab/request-states.skos.ttl` | `examples/request-record.jsonld` | `tests/test_request_profile_jsonld.py`, `tests/test_models.py` | Source state is preserved separately from normalised state. |
| Core event | `schemas/json/core-event.schema.json` | `foio:ProcessEvent`, `foio:hasEvidence`, `foio:assertionStatus`; `vocab/event-types.skos.ttl` | `examples/core-event.extension-notified.json`, `examples/core-event.deadline-calculated.json` | `tests/test_event_extraction_timeline.py`, `tests/test_transitions.py` | Candidate events cite evidence and assertion status. |
| Extraction contract | `schemas/json/extraction-contract.schema.json`, `schemas/json/consumer-extraction-contract.schema.json`, `contracts/foi-o-extraction-contract/0.1.0/manifest.json` | Pins `ontology/foi-o-nz.ttl`, the ontology-release manifest schema, and the candidate assertion-status vocabulary. | `examples/v2/schema-valid/extraction-contract-1.json`, three rejection fixtures, and four offline consumer fixtures | `tests/test_extraction_contract.py`, `tests/test_consumer_contracts.py`, `tests/test_empirical_schema_fixtures.py` | Consumers fail closed on unknown revisions; offline fixtures do not claim upstream approval; certification and promotion require human approval. |
| Re-extraction readiness | `schemas/json/reextraction-input-audit.schema.json` | Consumes the pinned extraction contract and archive provenance without changing ontology terms. | `examples/v2/reextraction-input-audit.fc27.json` | `tests/test_reextraction_input_audit.py` | Hash mismatch is rejected; incomplete rights metadata blocks extraction; raw source records are never modified. |
| Upstream extraction readiness | `schemas/json/upstream-extraction-readiness.schema.json` | Pins upstream archive and NLP implementation evidence without importing or promoting upstream outputs. | `examples/v2/upstream-extraction-readiness.2026-07-16.json` | `tests/test_upstream_extraction_readiness.py`, `tests/test_initial_baseline_verification.py` | Contract alignment, a content-bearing approved source, raw-manifest entry point, immutable initial candidate baseline, independent baseline verification, and model pin are verified; independent annotation and governed comparison remain pending. |
| Human promotion review | `schemas/json/human-promotion-review-packet.schema.json` | Keeps fixture, legal-mapping, and rights-scope decisions distinct and human-owned. | `examples/v2/human-promotion-review-packet.approved.json` | `tests/test_human_promotion_review_packet.py` | Candidate artifacts are SHA-256 pinned; `edithatogo` approved all four review items on 2026-07-16; schema-valid contract examples remain explicitly excluded as approval evidence. |
| OIA event-time candidates | `schemas/json/oia-event-time-fixture-set.schema.json` | Exercises the existing `oia_rules` decision identifiers without changing legal mappings. | `tests/fixtures/oia_rules/oia-event-time-independent-candidates.json` | `tests/test_oia_rules_independent_fixtures.py` | Candidate cases pin and remain disjoint from the approved authoring fixture; promotion is forbidden pending independent human calculation and review. |
| Source triangulation | `schemas/json/source-triangulation-result.schema.json` | Relates candidate claim support to existing evidence assertions and normative sources without certifying either. | `examples/v2/source-triangulation.example.json` | `tests/test_source_triangulation.py` | Two independent eligible sources are required; blocked, conflicting, stale, rights-uncertain, and insufficient evidence enter a deterministic human exception queue; promotion is always false. |
| Raw-state audit readiness | `schemas/json/raw-state-audit-readiness.schema.json` | Tests whether immutable FYI state observations have the correspondence and attachment evidence needed to review candidate mappings. | `examples/v2/raw-state-audit-readiness.fc27.json` | `tests/test_raw_state_audit.py` | Input and mapping hashes are verified; aggregate coverage only is committed; absent evidence blocks mapping conclusions. |
| NZ source rights and history | `schemas/json/source-rights-registry.schema.json` | Candidate rights classifications and the official OIA version sequence support later source-pack review without certifying reuse or event-time applicability. | `mappings/nz-source-rights-registry.yaml`, `mappings/nz-oia-version-index.yaml` | `tests/test_source_rights_registry.py` | Provider pages and 50 official OIA PDFs are hash-pinned; every entry remains pending human rights/applicability review. |
| Human certification | `schemas/json/core-event.schema.json`, `schemas/json/agent-action.schema.json` | `foio:DecisionLikeEvent`, `foio:HumanCertification`, `foio:machineCertificationAllowed`; `foio:DecisionLikeEventShape` | `examples/agent-action.search-plan.json`, `examples/review-task.risk.json` | `tests/test_agent_policy.py`, `tests/test_shacl_safety_profiles.py` | Agents cannot certify decision-like outcomes. |
| Legal source versioning | `schemas/json/process-advice.schema.json`, mapping YAML | `foio:LegalSourceVersion`, `foio:sourceVersionId` | `mappings/nz-legislation-sources.yaml` | `tests/test_legal_sources.py` | Live source refresh is an external gate. |
| PSC reporting | `schemas/json/reporting-metric.schema.json`, `schemas/json/psc-report.schema.json` | `foio:ReportingMetric` | `examples/reporting-metric.completed-requests.json`, `examples/psc-report.small.json` | `tests/test_reporting.py`, `tests/test_reporting_docs.py` | Public-data derivability is not official reporting. |
| Publication metadata | `schemas/json/release-checklist.schema.json`, `schemas/json/repository-release-metadata.schema.json` | `foio:DatasetPublication`, `foio:PermissionPolicy`, `foio:publicationCaveat` | `examples/release-checklist.v0.9.0.json`, `examples/repository-release-metadata.v0.9.0.json` | `tests/test_release_package.py`, `tests/test_publication_metadata.py` | Registry and publication approval remain human/external gates. |
| Generated assets | `schemas/json/generated-asset-manifest.schema.json`, `schemas/json/graph-export.schema.json`, `schemas/json/process-mining-ocel.schema.json`, `schemas/json/process-mining-conformance.schema.json`, `schemas/json/empirical-taskset-manifest.schema.json` | Graph node properties include semantic URI hints. | `examples/generated-asset-manifest.foi-o-publication.json`, `examples/graph-export.foi-o-evidence-network.json`, `examples/process-mining.fixture.ocel.json`, `examples/process-mining-conformance.fixture.json`, `examples/empirical-taskset-manifest.nz-first.json` | `tests/test_ontology_maturation_plan.py`, `tests/test_process_mining.py`, `tests/test_empirical_taskset_manifest.py` | Assets must include caption, text alternative, source inputs, command, and provenance. |

## Inventory Snapshot

| Artefact class | Count |
| --- | ---:|
| JSON Schema files | 74 |
| Example files | 131 |
| Documentation files | 52 |
| OWL ontology files | 1 |
| SHACL files | 1 |
| SKOS vocabulary files | 4 |
| Mapping files | 5 |
| Python test modules | 64 |

## Semantic Snapshot

| File | Key coverage |
| --- | --- |
| `ontology/foi-o-nz.ttl` | 21 OWL classes, 9 object properties, and 17 datatype properties. |
| `shacl/foi-o-nz.shapes.ttl` | 6 node shapes. |
| `vocab/request-states.skos.ttl` | 17 SKOS concepts. |
| `vocab/event-types.skos.ttl` | 15 SKOS concepts. |
| `vocab/assertion-status.skos.ttl` | 5 SKOS concepts. |
| `vocab/agent-boundaries.skos.ttl` | 3 SKOS concepts. |
