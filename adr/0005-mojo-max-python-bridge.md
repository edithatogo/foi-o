# ADR 0005: Mojo/MAX-first with Python data bridge

## Status

Accepted for v0.1 scaffold.

## Context

FOI-O NZ aims to be a bleeding-edge agent-facing infrastructure project. Mojo/MAX is attractive for deterministic kernels and future local AI workloads, but the immediate data-engine requirements are manifest ingestion, JSONL/Parquet export, schema validation, RDF parsing, and analytical summaries.

## Decision

- Use Mojo/MAX as a first-class experimental compiled core.
- Keep the core Mojo surface small and deterministic until syntax/tooling stabilise.
- Use Python with Polars/DuckDB/LanceDB as the mature data-control plane.
- Add CI jobs for both Python and Mojo.

## Consequences

This avoids anchoring the project to experimental dataframe tooling while preserving a clear path to Mojo-native acceleration.
