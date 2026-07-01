"""Dependency-light local microbenchmarks for deterministic FOI-O NZ kernels."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter_ns
from typing import Any

from foi_o_nz.chunks import chunk_request_record
from foi_o_nz.io import write_json
from foi_o_nz.ledger import build_ledger_entries
from foi_o_nz.risk import assess_record_risk
from foi_o_nz.state_machine import map_alaveteli_state


def _fixture_records(n: int) -> list[dict[str, Any]]:
    return [
        {
            "request_id": idx,
            "title": f"Request {idx} about planning, privacy and public services",
            "authority": "Example Ministry",
            "source_state": "successful" if idx % 3 == 0 else "waiting_response",
            "normalised_state": "Received",
            "messages": [
                {"body": "Please consult where privacy or commercial confidence is relevant."}
            ],
        }
        for idx in range(n)
    ]


def _time_ns(fn) -> tuple[Any, int]:  # type: ignore[no-untyped-def]
    start = perf_counter_ns()
    result = fn()
    return result, perf_counter_ns() - start


def run_local_benchmarks(*, iterations: int = 1_000) -> dict[str, Any]:
    """Run simple deterministic benchmarks with no optional dependencies."""
    records = _fixture_records(iterations)
    _, state_ns = _time_ns(lambda: [map_alaveteli_state(str(record["source_state"])) for record in records])
    chunks, chunk_ns = _time_ns(lambda: [chunk_request_record(record) for record in records])
    _, ledger_ns = _time_ns(lambda: build_ledger_entries([chunk.model_dump(mode="json") for chunk in chunks], record_type="chunk"))
    _, risk_ns = _time_ns(lambda: [assess_record_risk(record, sequence=idx) for idx, record in enumerate(records)])

    def per_second(ns: int) -> float:
        if ns == 0:
            return float("inf")
        return round(iterations / (ns / 1_000_000_000), 2)

    return {
        "schema_version": "foi-o-nz.benchmark.v0.1.0",
        "iterations": iterations,
        "benchmarks": {
            "map_state": {"elapsed_ns": state_ns, "records_per_second": per_second(state_ns)},
            "chunk_request": {"elapsed_ns": chunk_ns, "records_per_second": per_second(chunk_ns)},
            "ledger_hash": {"elapsed_ns": ledger_ns, "records_per_second": per_second(ledger_ns)},
            "risk_scan": {"elapsed_ns": risk_ns, "records_per_second": per_second(risk_ns)},
        },
        "notes": [
            "Microbenchmarks are local smoke indicators, not formal performance claims.",
            "Run on target hardware and compare against Mojo kernels before making acceleration claims.",
        ],
    }


def write_local_benchmarks(output: Path, *, iterations: int = 1_000) -> dict[str, Any]:
    """Run and write local benchmark results."""
    result = run_local_benchmarks(iterations=iterations)
    write_json(output, result)
    return {"ok": True, "output": str(output), "iterations": iterations}
