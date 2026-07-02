"""PSC reporting metric descriptors and derivability helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from foi_o_nz.models import ReportingMetric
from foi_o_nz.validation import load_json

DEFAULT_PSC_PROFILE = Path("mappings/psc-oia-statistics-profile.yaml")
DEFAULT_REPORTING_METRIC_SCHEMA = Path("schemas/json/reporting-metric.schema.json")


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
