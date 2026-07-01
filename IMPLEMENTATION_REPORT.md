# FOI-O NZ implementation report

Generated for the July 2026 scaffold handoff.

## Implemented surfaces

- Standalone repository scaffold for `edithatogo/foi-o-nz`.
- Python package `foi_o_nz` with CLI, Pydantic models, JSON Schema validation,
  FYI manifest normalisation, state mapping, analytics summaries, quality gates,
  RDF export, optional DuckDB materialisation, run-manifest provenance,
  transition audit, deterministic embeddings, optional LanceDB materialisation,
  JSON-LD context export, SHACL validation wrapper, generated-schema drift checks,
  and bounded agent-action policy records.
- Experimental Mojo package with deterministic state/certification kernels,
  mapping confidence, terminal-state checks, and machine working-day helpers.
- Optional FastMCP server exposing only bounded validation/state/quality tools.
- Ontology, SKOS, SHACL, JSON Schema, mappings, prompts, ADRs, docs, examples,
  tests, Makefile, Pixi config, and GitHub Actions CI.

## New v0.2 implementation pass

- Added indicative OIA clock annotations with explicit non-certification
  warnings.
- Added correspondence/message rule extraction for `MessageObserved` and
  candidate process events.
- Added event-stream quality gate that enforces evidence and human-certification
  boundary checks.
- Added RDF/Turtle export from request/event JSONL.
- Added JSONL schema validation command.
- Added run-manifest schema and output support.
- Added portable DuckDB SQL template and optional DuckDB builder.
- Added `.gitignore` and removed generated caches from the release bundle.

## New v0.3 implementation pass

- Added fast JSON encode/decode helpers using `orjson` with stdlib fallback.
- Added batch normalisation for multiple manifest files/directories/globs.
- Added deterministic feature-hashing embeddings and embedding-record schema.
- Added optional LanceDB table builder for vector/RAG experiments.
- Added transition-audit reporting and schema.
- Added JSON-LD context under `contexts/` and CLI export command.
- Added SHACL validation wrapper with pySHACL support and parse-only fallback.
- Added generated Pydantic schema export and shallow schema-drift checks.
- Added bounded FastMCP server module.
- Added rules-as-code agent-action policy templates and evaluator.
- Added extra tests covering batch, context, embeddings, transition audit, SHACL,
  schema generation, event-extraction evaluation, and agent policy.
- Expanded Mojo kernels/tests for mapping confidence and terminal states.

## Locally verified in this environment

```text
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
42 passed

PYTHONPATH=src python -m foi_o_nz.cli smoke-fixture --output-dir /tmp/foionz-v03-ci
PYTHONPATH=src python -m foi_o_nz.cli normalise-manifest --input ...
PYTHONPATH=src python -m foi_o_nz.cli validate-jsonl ...
PYTHONPATH=src python -m foi_o_nz.cli quality-gate ...
PYTHONPATH=src python -m foi_o_nz.cli transition-audit ...
PYTHONPATH=src python -m foi_o_nz.cli embed-jsonl ...
PYTHONPATH=src python -m foi_o_nz.cli export-rdf ...
PYTHONPATH=src python -m foi_o_nz.cli validate-shacl ...
PYTHONPATH=src python -m foi_o_nz.cli agent-action-template ...
PYTHONPATH=src python -m foi_o_nz.cli evaluate-agent-action ...
PYTHONPATH=src python -m foi_o_nz.cli schema-drift
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
```

## Not locally verified

The sandbox does not include the Modular Mojo/MAX toolchain, so Mojo formatting,
Mojo native tests, and Mojo binary build remain CI/operator checks after Pixi
installs the Modular packages. Optional Polars, DuckDB, LanceDB, pySHACL, and
FastMCP paths are implemented with explicit dependency errors or degraded mode;
only dependency-light paths were executed in this sandbox.

## Design boundary

The pasted Mojo notes are treated as a strategic direction, not a source of truth.
Mojo/MAX is used for deterministic kernels and future hot paths; Polars/DuckDB/
LanceDB remain the pragmatic data layer for ingestion and analysis until
Mojo-native dataframe/Arrow tooling is demonstrably production-ready.

## New v0.4 implementation pass

- Added tamper-evident JSONL ledgers with deterministic JSON canonicalisation,
  SHA-256 record hashes, and hash-chain verification.
- Added request/event chunk records for context-window planning, deterministic
  embeddings, and future vector stores.
- Added deterministic risk triage for privacy, health-information, withholding,
  consultation, and AI-workload review triggers. These outputs are review flags,
  not legal decisions.
- Added dataset metadata generation and Frictionless-style datapackage export.
- Added bounded OpenAPI 3.1 contract skeleton and agent tool/capability manifest.
- Added dependency-light local microbenchmarks for state mapping, chunking,
  ledger hashing, and risk scanning.
- Added Mojo text-planning/risk kernels and native tests.
- Expanded CI smoke commands and Makefile targets to cover v0.4 surfaces.

## Updated local verification for v0.4

```text
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
50 passed
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
repository validation ok
PYTHONPATH=src python -m foi_o_nz.cli schema-drift
ok with expected shallow warning-only drift for hand-authored schemas
```

## New v0.5 implementation pass

- Added deterministic chunk retrieval using BM25-style lexical scoring blended with
  local feature-hash vectors (`search-chunks`).
- Added redaction-candidate detection with hashed/masked previews only
  (`propose-redactions`). This does not redact, withhold, or decide.
- Added canonical JSONL stream diffs for incremental processing (`diff-jsonl`).
- Added request-scoped agent context packs that carry constraints, evidence,
  retrieval hits, risk triage, candidate redaction spans, and provenance
  (`build-agent-pack`).
- Added reproducibility manifests for selected artefacts and local tools
  (`repro-manifest`).
- Added new schemas and examples for retrieval results, redaction candidates,
  diff reports, agent packs, and reproducibility manifests.
- Expanded the bounded agent-action policy table to cover retrieval, candidate
  redaction detection, context-pack assembly, and stream diffs.
- Expanded the OpenAPI/tool manifest skeletons with retrieval, redaction-candidate,
  and agent-pack surfaces.
- Added Mojo retrieval scoring kernels and a native retrieval test file.

## Updated local verification for v0.5

```text
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
57 passed
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
repository validation ok
```

The v0.5 smoke path was also executed locally through normalisation, validation,
chunking, risk scanning, retrieval, redaction-candidate generation, agent-pack
assembly, stream diffing, and reproducibility-manifest generation.

## New v0.6 implementation pass

Added deterministic agent-infrastructure layers:

- content-addressed artifact manifests and JSONL record materialisation;
- convention-derived lineage graph export and Graphviz DOT output;
- deterministic local trace spans for artifact runs;
- goldset task generation for human annotation/evaluation;
- guardrail replay over event streams and agent-action streams;
- additional Mojo guardrail kernels for replay/status checks;
- optional `experiments` extra for structured extraction/evaluation packages.

The new Python commands are:

```text
foi-o-nz cas-manifest
foi-o-nz materialise-cas
foi-o-nz lineage-graph
foi-o-nz trace-artifacts
foi-o-nz build-goldset
foi-o-nz replay-guardrails
```

The dependency-light validation path passed locally:

```text
78 passed
repository validation ok
```

The Mojo/MAX and optional analytics/runtime paths are scaffolded for Pixi/CI but
not executed in this sandbox.


## New v0.6 extended implementation pass

Added further agent-infrastructure layers on top of the v0.6 CAS/lineage/replay work:

- human-review queues for risk, redaction-candidate, and certification-boundary signals;
- non-dispositive process-advice reports for request-scoped workflow support;
- neutral and Label Studio-compatible annotation task exports;
- request/event/chunk/risk graph export as JSON or Mermaid;
- Arrow/Polars/DuckDB-friendly analytical table contracts;
- local unsigned OCI image-layout materialisation for artefact bundles;
- static MCP planning bundle export with resources, prompts, and bounded tools;
- unsigned in-toto/SLSA-style artefact attestations;
- deterministic generic goldset sampling.

The new Python commands are:

```text
foi-o-nz build-review-queue
foi-o-nz process-advice
foi-o-nz export-annotation-tasks
foi-o-nz export-graph
foi-o-nz export-table-contracts
foi-o-nz materialise-oci
foi-o-nz export-mcp-bundle
foi-o-nz attest-artifacts
foi-o-nz sample-goldset
```

The dependency-light validation path passed locally:

```text
78 passed
repository validation ok
```

The agent boundary remains unchanged: all outputs are process-support, routing, provenance, evaluation, or publication-planning artefacts and cannot certify release, refusal, redaction, charging, extension, transfer, or review outcomes.

## New v0.7 implementation pass

Added a Mojo-first kernel facade with Python fallback as the executable
compatibility contract:

- `kernel_fallback.py` mirrors deterministic Mojo kernel semantics in pure Python.
- `native_kernel.py` discovers compiled Mojo kernel binaries, Mojo CLI, MAX CLI,
  Pixi, and Python fallback availability.
- `kernel-status`, `kernel-eval`, and `kernel-conformance` CLI commands expose the
  native/fallback boundary.
- Added native Mojo modules for transition diagnostics, non-cryptographic hashing,
  and redaction-candidate helper predicates.
- Added JSON Schemas/examples for kernel status and conformance reports.
- Added OpenAPI, tool-manifest, and MCP-bundle entries for bounded kernel
  introspection and conformance checks.

The key policy change is architectural rather than legal: deterministic logic is
now intended to be Mojo-first where the Modular toolchain is present, but Python
remains a tested fallback and does not become a legal decision engine.

The sandbox still cannot run native Mojo/MAX checks, so native tests remain CI or
operator verification paths. Python fallback/conformance tests were added so the
semantics remain stable in this environment.
