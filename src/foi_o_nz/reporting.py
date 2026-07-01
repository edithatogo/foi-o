"""Reporting metric descriptors and derivability helpers."""

from __future__ import annotations

from foi_o_nz.models import ReportingMetric

PSC_BASE_METRICS: tuple[ReportingMetric, ...] = (
    ReportingMetric(
        metric_id="psc.completed_requests",
        name="Completed OIA requests",
        source_profile="PSC OIA statistics",
        derivability="agency_internal_required",
        notes="Public FYI records can approximate public-platform completions but not whole-agency completions.",
    ),
    ReportingMetric(
        metric_id="psc.timeliness",
        name="Responses within legislative timeframe",
        source_profile="PSC OIA statistics",
        derivability="partially_derivable",
        notes="Requires authoritative received/decision dates and working-day calendars; public FYI dates may be incomplete.",
    ),
    ReportingMetric(
        metric_id="psc.extensions",
        name="Extensions notified",
        source_profile="PSC OIA statistics",
        derivability="partially_derivable",
        notes="May be extractable from correspondence, but absence in public text is not evidence of no extension.",
    ),
    ReportingMetric(
        metric_id="psc.transfers",
        name="Transfers",
        source_profile="PSC OIA statistics",
        derivability="partially_derivable",
        notes="May be extractable from messages; agency-internal partial transfers may be missing.",
    ),
    ReportingMetric(
        metric_id="psc.refusals",
        name="Refusals",
        source_profile="PSC OIA statistics",
        derivability="partially_derivable",
        notes="Public FYI state mapping is insufficient; needs decision-letter evidence and statutory basis extraction.",
    ),
    ReportingMetric(
        metric_id="psc.complaints",
        name="Ombudsman complaints",
        source_profile="PSC/Ombudsman complaints information",
        derivability="agency_internal_required",
        notes="FYI may show requester comments about complaints, but official complaint status comes from Ombudsman/agency reporting.",
    ),
)


def metric_table() -> list[dict[str, str]]:
    """Return PSC base metric descriptors as plain dictionaries."""
    return [metric.model_dump(mode="json") for metric in PSC_BASE_METRICS]
