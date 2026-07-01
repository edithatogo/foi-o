"""Shared FOI-O NZ constants."""

from __future__ import annotations

HUMAN_CERTIFICATION_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "HumanDecisionCertified",
        "DecisionCommunicated",
        "ReleaseMade",
        "RefusalCommunicated",
        "ChargeNoticeSent",
    }
)

SOURCE_SYSTEM_FYI_ARCHIVE = "fyi-archive-nz"
DEFAULT_JURISDICTION = "NZ"
DEFAULT_REGIME = "OIA"

CORE_EVENT_SCHEMA_VERSION = "foi-o-nz.core-event.v0.1.0"
REQUEST_PROFILE_SCHEMA_VERSION = "foi-o-nz.request-profile.v0.1.0"
AGENT_ACTION_SCHEMA_VERSION = "foi-o-nz.agent-action.v0.1.0"
REPORTING_METRIC_SCHEMA_VERSION = "foi-o-nz.reporting-metric.v0.1.0"
