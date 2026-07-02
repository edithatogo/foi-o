from __future__ import annotations

from pathlib import Path

from foi_o_nz.io import write_json
from foi_o_nz.reporting import (
    build_psc_aggregate_report,
    load_psc_reporting_profile,
    metric_table,
    validate_psc_reporting_profile,
    write_psc_aggregate_report,
)
from foi_o_nz.validation import validate_json_schema

PROFILE_PATH = Path("mappings/psc-oia-statistics-profile.yaml")
REPORTING_METRIC_SCHEMA = Path("schemas/json/reporting-metric.schema.json")
PSC_REPORT_SCHEMA = Path("schemas/json/psc-report.schema.json")


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
    metric_ids = {metric["metric_id"] for metric in metrics}
    derivability = {metric["derivability"] for metric in metrics}

    assert {
        "psc.completed_requests",
        "psc.timeliness",
        "psc.published_responses",
        "psc.extensions",
        "psc.transfers",
        "psc.refusals",
        "psc.average_time_to_respond",
        "psc.ombudsman_complaints",
    } <= metric_ids
    assert {
        "public_fyi_derivable",
        "partially_derivable",
        "agency_internal_required",
        "not_derivable",
    } <= derivability
    non_derivable = [metric for metric in metrics if metric["derivability"] == "not_derivable"]
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


def test_build_psc_aggregate_report_flags_derivability_boundaries(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        "\n".join(
            [
                '{"event_type":"RequestObserved","request_id":"100"}',
                '{"event_type":"DecisionCommunicated","request_ref":{"source_request_id":100}}',
                '{"event_type":"ExtensionNotified","request_id":"100"}',
                '{"event_type":"ComplaintObserved","request_id":"100"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_psc_aggregate_report(events)
    metrics = {metric["metric_id"]: metric for metric in report["metrics"]}

    assert report["schema_version"] == "foi-o-nz.psc-report.v0.1.0"
    assert report["input_event_count"] == 4
    assert metrics["fyi.public_platform_requests"]["value"] == 1
    assert metrics["psc.completed_requests"]["status"] == "partial_indicator"
    assert metrics["psc.completed_requests"]["value"] == 1
    assert metrics["psc.ombudsman_complaints"]["status"] == "agency_internal_required"
    assert metrics["psc.ombudsman_complaints"]["value"] is None
    assert metrics["psc.ombudsman_complaints"]["public_indicator_count"] == 1
    assert metrics["psc.processing_costs"]["status"] == "not_derivable"
    assert metrics["psc.processing_costs"]["value"] is None
    assert metrics["psc.processing_costs"]["event_count"] == 0
    assert all(metric["official_reporting_caveat"] for metric in report["metrics"])
    assert any("not official PSC reporting" in item for item in report["limitations"])


def test_write_psc_aggregate_report_validates_against_schema(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    output = tmp_path / "psc-report.json"
    events.write_text(
        '{"event_type":"RequestObserved","request_id":"100"}\n',
        encoding="utf-8",
    )

    report = write_psc_aggregate_report(events, output)

    assert report["output"] == str(output)
    validation = validate_json_schema(output, PSC_REPORT_SCHEMA)
    assert validation.ok, validation.errors
