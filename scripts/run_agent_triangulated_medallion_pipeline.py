#!/usr/bin/env python3
"""CLI script to run autonomous agent-triangulated Medallion pipeline.

Processes Bronze raw records for Australia and NZ, executes independent multi-agent
triangulation passes, normalizes to Silver requests and events, and generates Gold process
models (PNML Petri Nets, BPMN XML, XES logs, OCEL JSON) and transition matrices without human annotators.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from foi_o_nz.agent_triangulated_medallion import (
    MedallionRecord,
    run_agent_triangulated_medallion_pipeline,
)
from foi_o_nz.io import iter_jsonl


def _generate_sample_bronze_records(
    jurisdiction_filter: str | None = None,
) -> list[MedallionRecord]:
    """Generate representative sample Bronze records for NZ and all 9 AU jurisdictions."""
    jurisdictions_data = [
        (
            "NZ",
            "OIA",
            "Ministry of Health",
            "Ministry of Health request for clinical trial results. All documents released in full on 2026-03-01.",
            "2026-02-01",
            "2026-02-25",
        ),
        (
            "NZ",
            "LGOIMA",
            "Auckland Council",
            "Auckland Council stormwater infrastructure assessment. Access granted in full.",
            "2026-01-10",
            "2026-01-28",
        ),
        (
            "AU-CTH",
            "FOI",
            "Department of Finance",
            "Department of Finance request for budget estimations. Partially released with s47E redactions.",
            "2026-03-01",
            "2026-03-24",
        ),
        (
            "AU-NSW",
            "GIPA",
            "Transport for NSW",
            "Transport for NSW request for timetable modeling. Formally received and searching commenced.",
            "2026-04-01",
            "2026-04-18",
        ),
        (
            "AU-VIC",
            "FOI",
            "Department of Premier and Cabinet",
            "Department of Premier and Cabinet request. Access granted in full with public schedule.",
            "2026-05-01",
            "2026-05-20",
        ),
        (
            "AU-QLD",
            "RTI",
            "Queensland Health",
            "Queensland Health procurement documentation. Redacted under schedule 3 exemptions; partially released.",
            "2026-06-01",
            "2026-06-22",
        ),
        (
            "AU-WA",
            "FOI",
            "Main Roads WA",
            "Main Roads WA construction assessment report. Search completed and all records provided in full.",
            "2026-07-01",
            "2026-07-28",
        ),
        (
            "AU-SA",
            "FOI",
            "Department for Infrastructure and Transport",
            "Department for Infrastructure and Transport request. Notice of refusal issued under clause 6.",
            "2026-08-01",
            "2026-08-25",
        ),
        (
            "AU-TAS",
            "RTI",
            "Department of State Growth",
            "Department of State Growth tourism data request. Acknowledged and received.",
            "2026-09-01",
            "2026-09-15",
        ),
        (
            "AU-ACT",
            "FOI",
            "ACT Health Directorate",
            "ACT Health Directorate clinical operations data. Full release authorized.",
            "2026-10-01",
            "2026-10-18",
        ),
        (
            "AU-NT",
            "Information",
            "Territory Families",
            "Territory Families operational review. Searching records across regional centers.",
            "2026-11-01",
            "2026-11-20",
        ),
    ]

    records: list[MedallionRecord] = []
    for index, (jur, regime, auth, text, rec_d, dec_d) in enumerate(jurisdictions_data, start=1):
        if (
            jurisdiction_filter
            and jur.upper() != jurisdiction_filter.upper()
            and jurisdiction_filter.upper() != "ALL"
        ):
            continue
        records.append(
            MedallionRecord(
                record_id=f"rec-{jur.lower()}-{index:03d}",
                jurisdiction=jur,
                regime=regime,
                authority_name=auth,
                source_url=f"https://archive.publicrecords.org/{jur.lower()}/{index}",
                raw_text=text,
                source_metadata={"scrape_batch": "2026-08", "harvester": "fyi-cli"},
                event_time=f"{dec_d}T10:00:00Z",
                received_date=rec_d,
                decision_date=dec_d,
            )
        )
    return records


def _load_custom_bronze_records(
    input_dir: Path, jurisdiction_filter: str | None = None
) -> list[MedallionRecord]:
    """Load Bronze records from JSONL files in directory."""
    records: list[MedallionRecord] = []
    for jsonl_file in sorted(input_dir.glob("*.jsonl")):
        for raw in iter_jsonl(jsonl_file):
            jur = raw.get("jurisdiction", "NZ")
            if (
                jurisdiction_filter
                and jur.upper() != jurisdiction_filter.upper()
                and jurisdiction_filter.upper() != "ALL"
            ):
                continue
            records.append(
                MedallionRecord(
                    record_id=str(
                        raw.get("record_id") or raw.get("id") or f"rec-{len(records) + 1}"
                    ),
                    jurisdiction=jur,
                    regime=str(raw.get("regime", "OIA")),
                    authority_name=str(raw.get("authority_name") or raw.get("authority", "")),
                    source_url=str(raw.get("source_url", "")),
                    raw_text=str(
                        raw.get("raw_text") or raw.get("text") or raw.get("description", "")
                    ),
                    source_metadata=dict(raw.get("source_metadata", {})),
                    event_time=str(raw.get("event_time", "")),
                    received_date=str(raw.get("received_date", "")),
                    decision_date=str(raw.get("decision_date", "")),
                )
            )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute autonomous agent-triangulated Medallion pipeline (Bronze -> Silver -> Gold)"
    )
    parser.add_argument(
        "--jurisdiction",
        type=str,
        default="ALL",
        help="Jurisdiction filter (e.g. AU-NSW, NZ, or ALL)",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Optional directory containing raw Bronze JSONL files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/medallion_output"),
        help="Directory to save Bronze, Silver, Gold, and Analytics artifacts",
    )
    parser.add_argument(
        "--min-agents",
        type=int,
        default=2,
        help="Minimum agreeing independent agents required for consensus",
    )
    parser.add_argument(
        "--no-duckdb",
        action="store_true",
        help="Disable optional DuckDB database generation",
    )
    args = parser.parse_args()

    if args.input_dir and args.input_dir.exists():
        bronze_records = _load_custom_bronze_records(args.input_dir, args.jurisdiction)
        print(f"Loaded {len(bronze_records)} Bronze records from {args.input_dir.resolve()}")
    else:
        bronze_records = _generate_sample_bronze_records(args.jurisdiction)
        print(
            f"Generated {len(bronze_records)} representative Bronze records across jurisdictions."
        )

    if not bronze_records:
        print("No Bronze records found matching selection criteria.")
        return 1

    summary = run_agent_triangulated_medallion_pipeline(
        bronze_records=bronze_records,
        output_dir=args.output_dir,
        min_supporting_agents=args.min_agents,
        export_duckdb=not args.no_duckdb,
    )

    print("\n==================================================================")
    print("   AUTONOMOUS AGENT-TRIANGULATED MEDALLION PIPELINE & MODELING")
    print("==================================================================")
    print(f"Jurisdictions Processed:    {', '.join(summary.jurisdictions_processed)}")
    print(f"Bronze Records Ingested:    {summary.bronze_record_count}")
    print(f"Silver Requests Normalized: {summary.silver_request_count}")
    print(f"Silver Events Triangulated: {summary.silver_event_count}")
    print(f"Gold Process Models:        {summary.gold_model_count}")
    print(f"Agent Consensus Rate:       {summary.agent_consensus_rate:.1%}")
    print(f"Output Artifacts:           {summary.output_directory.resolve()}")
    print("==================================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
