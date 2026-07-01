# Implementation delta v0.4

This pass adds agent-foundation artifacts that strengthen integrity, reviewability,
and interoperability without making optional Mojo/MAX or vector dependencies
mandatory for day-one validation.

## Added code surfaces

- `foi_o_nz.ledger`: deterministic SHA-256 JSON canonicalisation and hash-chain
  ledgers for request/event/chunk/embedding JSONL streams.
- `foi_o_nz.chunks`: request/event chunk generation for context-window planning,
  deterministic embeddings, and future LanceDB indexes.
- `foi_o_nz.risk`: deterministic review-trigger triage for privacy, health,
  withholding/redaction, consultation, and AI-workload signals. This is explicitly
  not legal classification.
- `foi_o_nz.dataset_metadata`: FOI-O NZ metadata, Frictionless-style
  datapackages, Croissant-style JSON-LD, and Hugging Face dataset-card
  scaffolds for derived artifacts.
- `foi_o_nz.openapi`: bounded OpenAPI 3.1 skeleton for a future local agent API.
- `foi_o_nz.tool_manifest`: bounded tool/capability manifest derived from the
  rules-as-code agent policy table.
- `foi_o_nz.benchmarks`: dependency-light microbenchmarks for deterministic
  kernels, used only as local smoke indicators.

## Added CLI commands

```bash
foi-o-nz chunk-jsonl
foi-o-nz build-ledger
foi-o-nz verify-ledger
foi-o-nz risk-scan
foi-o-nz dataset-metadata   # default, --frictionless, --croissant, or --hf-card
foi-o-nz export-openapi
foi-o-nz export-tool-manifest
foi-o-nz benchmark-local
```

## Added schemas and examples

```text
schemas/json/chunk-record.schema.json
schemas/json/dataset-metadata.schema.json
schemas/json/ledger-entry.schema.json
schemas/json/risk-assessment.schema.json
examples/chunk-record.request.json
examples/dataset-metadata.examples.json
examples/ledger-entry.chunk.json
examples/risk-assessment.chunk.json
```

## Mojo additions

Added `mojo/foi_o_nz/text.mojo` with deterministic text-planning/risk helpers:

- `token_estimate_from_chars`
- `risk_level_from_score`
- `review_required_for_score`
- `can_machine_certify_safety_class`

The Mojo test task now includes `mojo/tests/test_text.mojo`.

## Validation status

Dependency-light validation completed locally:

```text
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
50 passed
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
repository validation ok
```

Mojo/MAX, Polars, DuckDB, LanceDB, pySHACL, FastMCP, and Ruff remain CI/operator
validated surfaces because those optional toolchains are not installed in the
current sandbox.

## Design note

The v0.4 changes are deliberately infrastructure-heavy rather than model-heavy.
The goal is to make the world safer for agents before adding stronger extraction
or inference: agents can verify source ledgers, consume chunks, run risk triage,
inspect tool boundaries, and operate against OpenAPI/MCP-style contracts, but
nothing in v0.4 allows them to certify OIA decisions.
