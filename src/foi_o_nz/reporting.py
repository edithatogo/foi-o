"""PSC reporting metric descriptors and derivability helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from foi_o_nz.io import iter_jsonl, write_json
from foi_o_nz.models import ReportingMetric
from foi_o_nz.validation import load_json

DEFAULT_PSC_PROFILE = Path("mappings/psc-oia-statistics-profile.yaml")
DEFAULT_REPORTING_METRIC_SCHEMA = Path("schemas/json/reporting-metric.schema.json")
PSC_REPORT_SCHEMA_VERSION = "foi-o-nz.psc-report.v0.1.0"
PSC_REPORT_LIMITATIONS = [
    "FOI-O NZ aggregate reports are not official PSC reporting.",
    "Values are public FYI-derived indicators from the supplied event stream only.",
    "Partial, agency-internal-required, and not-derivable metrics must not be used as official performance statistics.",
]


def load_psc_reporting_profile(path: Path = DEFAULT_PSC_PROFILE) -> dict[str, Any]:
    """Load the source PSC reporting profile and normalise metrics to a list."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping object in {path}")
    metrics = data.get("metrics")
    if isinstance(metrics, dict):
        normalised = []
        for metric_id, metric in metrics.items():
            if not isinstance(metric, dict):
                raise ValueError(f"metrics.{metric_id}: expected mapping")
            record = {"metric_id": str(metric_id), **metric}
            normalised.append(record)
        data = {**data, "metrics": normalised}
    elif not isinstance(metrics, list):
        raise ValueError(f"Expected metrics list or mapping in {path}")
    return data


def metric_table(path: Path = DEFAULT_PSC_PROFILE) -> list[dict[str, Any]]:
    """Return PSC reporting metric descriptors as schema-aligned dictionaries."""
    profile = load_psc_reporting_profile(path)
    return [
        ReportingMetric.model_validate(metric).model_dump(mode="json", exclude_none=True)
        for metric in profile["metrics"]
    ]


def validate_psc_reporting_profile(
    path: Path = DEFAULT_PSC_PROFILE,
    schema_path: Path = DEFAULT_REPORTING_METRIC_SCHEMA,
) -> dict[str, Any]:
    """Validate all PSC reporting profile metrics against the JSON Schema."""
    profile = load_psc_reporting_profile(path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    derivability_counts: dict[str, int] = {}
    metric_ids: set[str] = set()
    for index, metric in enumerate(profile["metrics"]):
        try:
            record = ReportingMetric.model_validate(metric).model_dump(
                mode="json", exclude_none=True
            )
        except ValueError as exc:
            errors.append(f"metrics.{index}: {exc}")
            continue
        metric_id = record["metric_id"]
        if metric_id in metric_ids:
            errors.append(f"metrics.{index}.metric_id: duplicate {metric_id}")
        metric_ids.add(metric_id)
        derivability = record["derivability"]
        derivability_counts[derivability] = derivability_counts.get(derivability, 0) + 1
        if record["derivability"] == "not_derivable" and record["event_dependencies"]:
            errors.append(f"metrics.{index}.event_dependencies: must be empty when not_derivable")
        if "not official PSC reporting" not in record["official_reporting_caveat"]:
            errors.append(
                f"metrics.{index}.official_reporting_caveat: must state not official PSC reporting"
            )
        for error in sorted(
            validator.iter_errors(record), key=lambda item: list(item.absolute_path)
        ):
            path_text = ".".join(str(part) for part in error.absolute_path) or "<root>"
            errors.append(f"metrics.{index}.{path_text}: {error.message}")
    return {
        "ok": not errors,
        "schema_version": profile.get("schema_version"),
        "metric_count": len(profile["metrics"]),
        "metric_ids": sorted(metric_ids),
        "derivability_counts": dict(sorted(derivability_counts.items())),
        "errors": errors,
    }


def build_psc_aggregate_report(
    events_path: Path,
    *,
    profile_path: Path = DEFAULT_PSC_PROFILE,
) -> dict[str, Any]:
    """Build a deterministic PSC-style aggregate report from public event JSONL."""
    profile = load_psc_reporting_profile(profile_path)
    events = list(iter_jsonl(events_path))
    metrics = [_aggregate_metric(metric, events) for metric in metric_table(profile_path)]
    return {
        "schema_version": PSC_REPORT_SCHEMA_VERSION,
        "profile_schema_version": profile.get("schema_version"),
        "source_profile": profile.get("source"),
        "source_url": profile.get("source_url"),
        "input": str(events_path),
        "input_event_count": len(events),
        "metric_count": len(metrics),
        "metrics": metrics,
        "limitations": PSC_REPORT_LIMITATIONS,
    }


def write_psc_aggregate_report(
    events_path: Path,
    output: Path,
    *,
    profile_path: Path = DEFAULT_PSC_PROFILE,
) -> dict[str, Any]:
    """Write a deterministic PSC-style aggregate report."""
    report = build_psc_aggregate_report(events_path, profile_path=profile_path)
    report = {**report, "output": str(output)}
    write_json(output, report)
    return report


def _aggregate_metric(metric: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    dependencies = set(metric["event_dependencies"])
    matches = [event for event in events if str(event.get("event_type") or "") in dependencies]
    request_ids = sorted(
        {request_id for event in matches if (request_id := _event_request_id(event)) is not None}
    )
    derivability = metric["derivability"]
    if derivability == "public_fyi_derivable":
        status = "derived_public_indicator"
        value: int | None = len(request_ids) if request_ids else len(matches)
        public_indicator_count = value
        warnings = [
            "public_fyi_indicator_only: count is limited to the supplied public event stream"
        ]
    elif derivability == "partially_derivable":
        status = "partial_indicator"
        value = len(request_ids) if request_ids else len(matches)
        public_indicator_count = value
        warnings = [
            "partial_indicator_not_official_report: public data may omit agency-internal records"
        ]
    elif derivability == "agency_internal_required":
        status = "agency_internal_required"
        value = None
        public_indicator_count = len(request_ids) if request_ids else len(matches)
        warnings = [
            "agency_internal_required_for_official_metric: public observations are context only"
        ]
    else:
        status = "not_derivable"
        value = None
        public_indicator_count = 0
        warnings = ["not_derivable_from_public_fyi_data"]
    return {
        "metric_id": metric["metric_id"],
        "name": metric["name"],
        "derivability": derivability,
        "status": status,
        "value": value,
        "public_indicator_count": public_indicator_count,
        "event_count": len(matches),
        "request_count": len(request_ids),
        "event_dependencies": metric["event_dependencies"],
        "matched_event_types": sorted({str(event.get("event_type") or "") for event in matches}),
        "public_data_limitations": metric["public_data_limitations"],
        "exclusions": metric["exclusions"],
        "official_reporting_caveat": metric["official_reporting_caveat"],
        "warnings": warnings,
    }


def _event_request_id(event: dict[str, Any]) -> str | None:
    request_id = event.get("request_id")
    if request_id not in {None, ""}:
        return str(request_id)
    request_ref = event.get("request_ref")
    if isinstance(request_ref, dict):
        source_request_id = request_ref.get("source_request_id")
        if source_request_id not in {None, ""}:
            return str(source_request_id)
    return None
