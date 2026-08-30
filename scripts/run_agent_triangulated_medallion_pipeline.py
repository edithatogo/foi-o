#!/usr/bin/env python3
"""CLI script to run autonomous agent-triangulated Medallion pipeline.

Processes Bronze raw records for Australia and NZ, executes independent multi-agent
triangulation passes, normalizes to Silver events, and generates Gold process
models (PNML Petri Nets, BPMN XML, XES logs) without human annotators.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from foi_o_nz.agent_triangulated_medallion import (
    MedallionRecord,
    run_agent_triangulated_medallion_pipeline,
)


def _generate_sample_bronze_records() -> list[MedallionRecord]:
    """Generate representative sample Bronze records for NZ and all 9 AU jurisdictions."""
    jurisdictions_data = [
        (
            "NZ",
            "OIA",
            "Ministry of Health request for clinical trial results. All documents released in full on 2026-03-01.",
        ),
        (
            "AU-CTH",
            "FOI",
            "Department of Finance request for budget estimations. Partially released with s47E redactions.",
        ),
        (
            "AU-NSW",
            "GIPA",
            "Transport for NSW request for timetable modeling. Formally received and searching commenced.",
        ),
        (
            "AU-VIC",
            "FOI",
            "Department of Premier and Cabinet request. Access granted in full with public schedule.",
        ),
        (
            "AU-QLD",
            "RTI",
            "Queensland Health procurement documentation. Redacted under schedule 3 exemptions; partially released.",
        ),
        (
            "AU-WA",
            "FOI",
            "Main Roads WA construction assessment report. Search completed and all records provided in full.",
        ),
        (
            "AU-SA",
            "FOI",
            "Department for Infrastructure and Transport request. Notice of refusal issued under clause 6.",
        ),
        (
            "AU-TAS",
            "RTI",
            "Department of State Growth tourism data request. Acknowledged and received.",
        ),
        (
            "AU-ACT",
            "FOI",
            "ACT Health Directorate clinical operations data. Full release authorized.",
        ),
        (
            "AU-NT",
            "Information",
            "Territory Families operational review. Searching records across regional centers.",
        ),
    ]

    records: list[MedallionRecord] = []
    for index, (jur, regime, text) in enumerate(jurisdictions_data, start=1):
        records.append(
            MedallionRecord(
                record_id=f"rec-{jur.lower()}-{index:03d}",
                jurisdiction=jur,
                regime=regime,
                source_url=f"https://archive.publicrecords.org/{jur.lower()}/{index}",
                raw_text=text,
                source_metadata={"scrape_batch": "2026-08", "harvester": "fyi-cli"},
                event_time=f"2026-08-{index:02d}T10:00:00Z",
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute autonomous agent-triangulated Medallion pipeline (Bronze -> Silver -> Gold)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/medallion_output"),
        help="Directory to save Bronze, Silver, and Gold artifacts",
    )
    parser.add_argument(
        "--min-agents",
        type=int,
        default=2,
        help="Minimum agreeing independent agents required for consensus",
    )
    args = parser.parse_args()

    bronze_records = _generate_sample_bronze_records()
    print(f"Loaded {len(bronze_records)} raw Bronze records across NZ and 9 AU jurisdictions.")

    summary = run_agent_triangulated_medallion_pipeline(
        bronze_records=bronze_records,
        output_dir=args.output_dir,
        min_supporting_agents=args.min_agents,
    )

    print("\n--- Autonomous Agent-Triangulated Medallion Pipeline Complete ---")
    print(f"Jurisdictions Processed: {', '.join(summary.jurisdictions_processed)}")
    print(f"Bronze Records:          {summary.bronze_record_count}")
    print(f"Silver Events (Consensus): {summary.silver_event_count}")
    print(f"Gold Process Models:     {summary.gold_model_count}")
    print(f"Agent Consensus Rate:    {summary.agent_consensus_rate:.1%}")
    print(f"Output Directory:        {summary.output_directory.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
