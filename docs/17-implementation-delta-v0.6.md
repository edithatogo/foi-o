# Implementation delta v0.6

This pass adds deterministic agent-infrastructure surfaces that make the FOI-O NZ
workspace more useful as a future agent-facing environment without allowing any
agent to certify OIA decisions.

## Added

### Content addressing, lineage, traces, and replay

- `foi_o_nz.cas`
- `foi_o_nz.lineage`
- `foi_o_nz.traces`
- `foi_o_nz.replay`
- CLI: `foi-o-nz cas-manifest`
- CLI: `foi-o-nz materialise-cas`
- CLI: `foi-o-nz lineage-graph`
- CLI: `foi-o-nz trace-artifacts`
- CLI: `foi-o-nz replay-guardrails`

These functions produce SHA-256 content manifests, local per-record CAS objects,
convention-derived lineage graphs, OpenTelemetry-inspired trace spans, and
certification-boundary guardrail replay reports. They provide integrity,
observability, and policy checking only; they do not certify legal correctness.

### Human-review routing and process advice

- `foi_o_nz.review_queue`
- `foi_o_nz.process_advice`
- `foi_o_nz.annotation`
- CLI: `foi-o-nz build-review-queue`
- CLI: `foi-o-nz process-advice`
- CLI: `foi-o-nz export-annotation-tasks`
- Schemas: `review-task`, `process-advice`, `annotation-task`

Candidate risk hits, candidate redaction spans, and uncertified dispositive events
can now be routed to explicit human-review worklists. The process-advice command
suggests safe preparatory next steps, missing artefacts, blocked actions, and
required human reviews. Annotation exports support neutral FOI-O JSONL and a
Label Studio-compatible JSON shape.

### Graph, table contracts, and publication-oriented bundles

- `foi_o_nz.graph_export`
- `foi_o_nz.table_contracts`
- `foi_o_nz.oci_layout`
- `foi_o_nz.mcp_bundle`
- CLI: `foi-o-nz export-graph`
- CLI: `foi-o-nz export-table-contracts`
- CLI: `foi-o-nz materialise-oci`
- CLI: `foi-o-nz export-mcp-bundle`
- Schemas: `graph-export`, `table-contracts`, `oci-layout-summary`, `mcp-bundle`

The graph export builds request/event/chunk/risk relationships as JSON or
Mermaid. Table contracts describe Arrow/Polars/DuckDB-friendly analytical tables.
The OCI layout writer creates a local, unsigned OCI image-layout directory for
future registry experiments. The MCP bundle exports resources, prompts, and tools
as a static planning artefact aligned with the project safety boundary.

### Goldset and evaluation support

- `foi_o_nz.goldset`
- CLI: `foi-o-nz build-goldset`
- CLI: `foi-o-nz sample-goldset`
- Schema: `goldset-task`
- Schema: `goldset-item`

The repo now supports both chunk/risk-derived goldset task creation and generic
deterministic stratified sampling over request/event/chunk/risk/review-task
streams. These are evaluation and annotation-planning artefacts, not claims of
statistical representativeness.

### Mojo additions

- `mojo/foi_o_nz/guardrail.mojo`
- `mojo/tests/test_guardrail.mojo`

The Mojo layer now includes simple deterministic kernels for dispositive event
classification, replay pass/fail status, severity rank, and review-required
classification. These are kept small and testable while the Mojo/MAX ecosystem is
rapidly changing.

### Optional experimental stack

The `experiments` optional extra remains the place for future structured
extraction and evaluation experiments using libraries such as Instructor,
Outlines, DSPy, LiteLLM, and OpenTelemetry. These are optional and are not on the
required validation path.

## Local verification

The dependency-light path was verified locally:

```bash
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
```

Result:

```text
78 passed
repository validation ok
```

Mojo/MAX, Polars, DuckDB, LanceDB, pySHACL, FastMCP, Ruff, and ty remain CI/operator
surfaces because this sandbox does not include those optional toolchains.
