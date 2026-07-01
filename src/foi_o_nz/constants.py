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

