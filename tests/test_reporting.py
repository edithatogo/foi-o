from __future__ import annotations

from pathlib import Path

from foi_o_nz.io import write_json
from foi_o_nz.reporting import (
    load_psc_reporting_profile,
    metric_table,
    validate_psc_reporting_profile,
)
from foi_o_nz.validation import validate_json_schema

PROFILE_PATH = Path("mappings/psc-oia-statistics-profile.yaml")
REPORTING_METRIC_SCHEMA = Path("schemas/json/reporting-metric.schema.json")


def test_psc_reporting_profile_metrics_validate_against_schema() -> None:
    report = validate_psc_reporting_profile(PROFILE_PATH, REPORTING_METRIC_SCHEMA)

    assert report["ok"], report["errors"]
    assert report["metric_count"] >= 8
    assert report["derivability_counts"]["partially_derivable"] >= 1
    assert report["derivability_counts"]["agency_internal_required"] >= 1
    assert report["derivability_counts"]["not_derivable"] >= 1


def test_reporting_profile_covers_public_partial_internal_and_not_derivable() -> None:
    profile = load_psc_reporting_profile(PROFILE_PATH)
    metrics = profile["metrics"]
    derivability = {metric["derivability"] for metric in metrics}

    assert {
        "public_fyi_derivable",
        "partially_derivable",
        "agency_internal_required",
        "not_derivable",
    } <= derivability
    non_derivable = [
        metric for metric in metrics if metric["derivability"] == "not_derivable"
    ]
    assert non_derivable
    assert all(metric["event_dependencies"] == [] for metric in non_derivable)
    assert all(metric["public_data_limitations"] for metric in non_derivable)


def test_metric_table_uses_reporting_metric_schema(tmp_path: Path) -> None:
    metrics = metric_table(PROFILE_PATH)

    assert metrics
    for metric in metrics:
        instance = tmp_path / f"{metric['metric_id'].replace('.', '-')}.json"
        write_json(instance, metric)
        validation = validate_json_schema(instance, REPORTING_METRIC_SCHEMA)
        assert validation.ok, validation.errors
        assert metric["official_reporting_caveat"]
        assert "not official PSC reporting" in metric["official_reporting_caveat"]
