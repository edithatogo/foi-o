# Implementation delta v0.3

This pass moves the scaffold from a planning/validation workbench toward a first
agent-facing analytical substrate.

## Added

- Fast JSON helper layer using `orjson` when available and a deterministic stdlib fallback.
- Batch manifest normalisation across multiple files, directories, and globs.
- Deterministic feature-hashing embeddings for request/event JSONL records.
- Optional LanceDB table materialisation for vector search experiments.
- Lifecycle transition audit reports over event streams.
- JSON-LD context export under `contexts/`.
- SHACL validation wrapper with pySHACL support and parse-only degraded mode.
- Pydantic schema export and shallow committed-schema drift checks.
- Optional bounded FastMCP server exposing validation/state/quality tools only.
- Rules-as-code agent-action policy templates and evaluation commands.
- Event-extraction evaluation helpers for gold-set precision/recall/F1.
- Additional JSON Schemas and examples for embedding records and transition audits.
- Expanded Mojo deterministic kernels for mapping confidence and terminal-state checks.

## Design notes

The embedding baseline is intentionally non-semantic. It is a local, reproducible
feature-hashing bridge that lets the vector-store and agent contracts be tested
without embedding service keys, model downloads, GPUs, or MAX runtime assumptions.
MAX/Hugging Face embeddings can later be added as alternative providers behind the
same embedding-record schema.

The MCP server is deliberately bounded. Its tools map states, validate JSON/JSONL,
and run quality gates. It does not expose any tool that can certify a legal outcome.

The SHACL command succeeds in parse-only mode if pySHACL is absent. CI can install
the `rdf` extra to turn this into full SHACL constraint validation.
