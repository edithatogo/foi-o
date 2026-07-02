"""Shared FOI-O NZ constants."""

from __future__ import annotations

HUMAN_CERTIFICATION_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "HumanDecisionCertified",
        "DecisionCommunicated",
        "ReleaseMade",
        "RefusalCommunicated",
        "ChargeNoticeSent",
        "ExtensionNotified",
        "TransferNotified",
    }
)

SOURCE_SYSTEM_FYI_ARCHIVE = "fyi-archive-nz"
DEFAULT_JURISDICTION = "NZ"
DEFAULT_REGIME = "OIA"

CORE_EVENT_SCHEMA_VERSION = "foi-o-nz.core-event.v0.1.0"
REQUEST_PROFILE_SCHEMA_VERSION = "foi-o-nz.request-profile.v0.1.0"
AGENT_ACTION_SCHEMA_VERSION = "foi-o-nz.agent-action.v0.1.0"
REPORTING_METRIC_SCHEMA_VERSION = "foi-o-nz.reporting-metric.v0.1.0"
LEDGER_SCHEMA_VERSION = "foi-o-nz.ledger.v0.1.0"
CHUNK_SCHEMA_VERSION = "foi-o-nz.chunk.v0.1.0"
RISK_ASSESSMENT_SCHEMA_VERSION = "foi-o-nz.risk-assessment.v0.1.0"
DATASET_METADATA_SCHEMA_VERSION = "foi-o-nz.dataset-metadata.v0.1.0"
RELEASE_CHECKLIST_SCHEMA_VERSION = "foi-o-nz.release-checklist.v0.1.0"
REPOSITORY_RELEASE_METADATA_SCHEMA_VERSION = "foi-o-nz.repository-release.v0.1.0"
RETRIEVAL_RESULT_SCHEMA_VERSION = "foi-o-nz.retrieval-result.v0.1.0"
REDACTION_CANDIDATE_SCHEMA_VERSION = "foi-o-nz.redaction-candidate.v0.1.0"
DIFF_SCHEMA_VERSION = "foi-o-nz.diff.v0.1.0"
AGENT_PACK_SCHEMA_VERSION = "foi-o-nz.agent-pack.v0.1.0"
REPRO_MANIFEST_SCHEMA_VERSION = "foi-o-nz.reproducibility.v0.1.0"
CAS_MANIFEST_SCHEMA_VERSION = "foi-o-nz.cas-manifest.v0.1.0"
LINEAGE_GRAPH_SCHEMA_VERSION = "foi-o-nz.lineage-graph.v0.1.0"
TRACE_SPAN_SCHEMA_VERSION = "foi-o-nz.trace-span.v0.1.0"
GOLDSET_TASK_SCHEMA_VERSION = "foi-o-nz.goldset-task.v0.1.0"
GUARDRAIL_REPLAY_SCHEMA_VERSION = "foi-o-nz.guardrail-replay.v0.1.0"
NATIVE_KERNEL_STATUS_SCHEMA_VERSION = "foi-o-nz.native-kernel-status.v0.1.0"
KERNEL_CONFORMANCE_SCHEMA_VERSION = "foi-o-nz.kernel-conformance.v0.1.0"

MOJO_AUDIT_SCHEMA_VERSION = "foi-o-nz.mojo-audit.v0.1.0"
KERNEL_MANIFEST_SCHEMA_VERSION = "foi-o-nz.kernel-manifest.v0.1.0"
KERNEL_READINESS_SCHEMA_VERSION = "foi-o-nz.kernel-readiness.v0.1.0"


REVIEW_TASK_SCHEMA_VERSION = "foi-o-nz.review-task.v0.1.0"
GRAPH_SCHEMA_VERSION = "foi-o-nz.graph.v0.1.0"
ANNOTATION_TASK_SCHEMA_VERSION = "foi-o-nz.annotation-task.v0.1.0"
PROCESS_ADVICE_SCHEMA_VERSION = "foi-o-nz.process-advice.v0.1.0"
GOLDSET_SCHEMA_VERSION = "foi-o-nz.goldset-item.v0.1.0"
ATTESTATION_SCHEMA_VERSION = "https://in-toto.io/Statement/v1"
