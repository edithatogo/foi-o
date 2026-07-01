# Pipelines

This directory records pipeline contracts rather than storing generated corpora.
Large outputs belong in `data/`, Hugging Face, Zenodo, OSF, or other archive surfaces.

## v0.1 pipeline

```text
FYI manifest JSON/JSONL
  -> request profiles JSONL
  -> core process events JSONL
  -> optional Parquet via Polars
  -> optional DuckDB summaries
  -> future LanceDB embeddings
```

## Data-engine decision

Use Polars/DuckDB for ingestion, query planning, and Parquet until Mojo-native dataframe/Arrow tooling is mature enough. Use Mojo for deterministic kernels and later hot-loop NLP functions where Python interop overhead would matter.
