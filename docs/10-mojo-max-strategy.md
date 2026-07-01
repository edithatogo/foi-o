# Mojo/MAX strategy

FOI-O NZ adopts a Mojo/MAX-first direction without pretending the Mojo data ecosystem is already a replacement for Polars/DuckDB.

## Decision

Use Mojo for:

- deterministic event/state kernels;
- certification-boundary predicates;
- future hot-loop NLP functions such as text normalisation, redaction-marker scanning, local tokenisation, and candidate-event scoring;
- future MAX-adjacent local inference/embedding experiments.

Use Python/Polars/DuckDB/LanceDB for:

- FYI manifest ingestion;
- JSONL/Parquet export;
- analytical summaries;
- vector indexing until a Mojo-native option is mature;
- RDF/SHACL/JSON Schema validation.

## Rationale

The first public value is not raw compute. It is a correct process contract: typed states, evidence, provenance, assertion status, reporting derivability, and human certification boundaries. Mojo should accelerate deterministic pieces once the semantics are stable.

## Stability labels

| Layer | Status | Notes |
| --- | --- | --- |
| Mojo stdlib and compiler tooling | First-party but moving | Keep code small and covered by CI. |
| MAX serving | First-party platform | Useful for future local extraction endpoints. |
| Polars/DuckDB | Production | Preferred for dataframes/querying now. |
| LanceDB | Useful optional extra | Suitable for future local embedding indexes. |
| MojoFrame and similar | Experimental | Track, but do not anchor v0.1 on it. |
