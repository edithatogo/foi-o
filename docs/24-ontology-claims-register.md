# FOI-O NZ ontology claims register

This register states what the current repository can support, what it cannot
support, and how broad FOI-O claims should be phrased.

| Claim | Status | Evidence | Required wording boundary |
| --- | --- | --- | --- |
| FOI-O is intended as a reusable method and conceptual frame for FOI process modelling. | Supported as design intent. | `README.md`, `docs/24-ontology-methods-protocol.md`, `docs/27-submission-manuscript.md` | Say "design intent" or "future validation path"; do not imply completed non-NZ validation. |
| FOI-O NZ is the only implemented and validated jurisdictional profile. | Supported. | `README.md`, `docs/01-foundations-register.md`, this register | Do not add or imply other validated country profiles. |
| The repository preserves source states separately from normalised states. | Supported by fixtures and tests. | `schemas/json/request-profile.schema.json`, `examples/request-record.jsonld`, `tests/test_request_profile_jsonld.py` | Treat mappings as process metadata, not legal conclusions. |
| Candidate process events can cite evidence and assertion status. | Supported by schemas and examples. | `schemas/json/core-event.schema.json`, `examples/core-event.extension-notified.json` | Candidate events remain reviewable signals. |
| Decision-like outcomes require human certification if final. | Supported by policy, SHACL, examples, and tests. | `docs/04-agent-boundaries.md`, `src/foi_o_nz/agent_policy.py`, `shacl/foi-o-nz.shapes.ttl`, `tests/test_agent_policy.py` | Do not describe agents as approving, refusing, redacting, extending, charging, transferring, or resolving complaints. |
| OIA clock calculations are indicative and source-aware. | Supported in fixture mode. | `docs/03-process-profile.md`, `examples/nz-public-holidays-2026.govt-nz.json`, `tests/test_dates.py` | Warn when holidays or regional calendars are incomplete. |
| Legal/guidance references can retain version and retrieval metadata. | Supported by repo-local mappings. | `docs/06-legal-versioning.md`, `mappings/nz-legislation-sources.yaml`, `tests/test_legal_sources.py` | Live source freshness remains external unless a source snapshot is supplied. |
| PSC-style public-data reporting can classify metric derivability. | Supported by profile and sample report. | `docs/21-psc-reporting-profile.md`, `examples/psc-report.small.json`, `tests/test_reporting.py` | Do not call outputs official PSC reporting. |
| The ontology/SKOS/SHACL layer is implemented for the NZ profile. | Supported by semantic tests. | `ontology/foi-o-nz.ttl`, `vocab/*.skos.ttl`, `shacl/foi-o-nz.shapes.ttl`, `tests/test_semantic_alignment.py` | Do not claim full legal ontology completeness. |
| The repository has a separate process model as well as an ontology. | Supported. | `docs/31-process-models.md`, `examples/state-machine.mmd`, `process_models/foi-o-nz-core.bpmn`, `process_models/foi-o-nz-core.pnml`, `tests/test_process_models.py` | Treat BPMN and Petri net files as review/interchange models, not legal decision systems. |
| Process-mining interchange artefacts exist for the NZ fixture path. | Supported as fixture interoperability only. | `docs/32-process-mining-fixtures.md`, `examples/process-mining-events.fixture.jsonl`, `examples/process-mining.fixture.xes`, `examples/process-mining.fixture.ocel.json`, `tests/test_process_mining.py` | Do not claim live-corpus conformance, agency performance, bottleneck frequencies, or empirical cycle-time findings. |
| NZ empirical annotation task sets are specified. | Supported as a plan only. | `examples/empirical-taskset-manifest.nz-first.json`, `schemas/json/empirical-taskset-manifest.schema.json`, `docs/20-corpus-profile-goldset.md` | Call them annotation task sets until source snapshots, human review, adjudication, and agreement evidence exist. |
| The publication package has local validation artefacts. | Supported in repo-local form. | `docs/23-methods-paper.md`, `docs/28-submission-supplement.md`, `examples/generated-asset-manifest.foi-o-publication.json` | Do not claim journal, arXiv, registry, or peer-review completion. |
| Gold sets exist for large-scale empirical claims. | Not yet supported. | `docs/07-evaluation-plan.md`, `docs/20-corpus-profile-goldset.md` | Call current planned sets annotation tasks until human review and adjudication evidence exist. |
| FOI-O works across other countries. | Not supported as an empirical claim. | No non-NZ profile in this repository. | Say future work or design intent only. |

## Fail-Closed Rule

If a claim cannot be tied to a repo-local path, deterministic validation command,
or recorded human/external evidence, phrase it as a limitation, planned task, or
external gate.
