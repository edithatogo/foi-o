# Implementation status

This status page separates implemented repo-local surfaces, experimental optional surfaces, planned roadmap work, and external gates. It supersedes the older v0.1-only status snapshot.

## Implemented and repo-local

- Python package `foi_o_nz` with Typer CLI entry points.
- Pydantic models and JSON Schemas for core events, request profiles, agent actions, reporting metrics, review tasks, manifests, kernel reports, and related records.
- FYI/Alaveteli state mapping, JSON/JSONL manifest normalisation, event analytics, transition audit, quality gates, and schema validation helpers.
- RDF/Turtle export, JSON-LD context export, FOIO namespace, expanded ontology terms, SKOS vocabularies, SHACL safety profiles, semantic export alignment, and SHACL parse/degraded-mode wrapper.
- Deterministic embeddings, chunking, lexical/vector-style retrieval, optional LanceDB table/search fallback, redaction candidates, risk scans, stream diffs, agent packs, ledgers, reproducibility manifests, CAS, lineage, traces, review queues, process advice, annotation tasks, graph export, table contracts, OCI layout summaries, attestations, and MCP bundle scaffolds.
- Fixture-backed FYI corpus profiling, source-state preservation, request JSON-LD completion, and reproducible 100-request goldset sampling/task exports.
- Observed correspondence event extraction, deterministic timeline reconstruction, confidence/provenance retention, and evaluation fixtures.
- Source-aware NZ holiday calendars, OIA summer-exclusion clock handling, source-versioned legal/guidance references, and process-rule quality gates.
- Hardened read-only MCP/tool contract descriptors, unsafe-tool rejection, and optional runtime degradation tests.
- Candidate-only local/MAX extraction request packs with provider provenance, human-review routing, generated-output exclusion, and unsafe machine-certification rejection.
- Python fallback kernel contract, native-kernel discovery/status reports, conformance reports, static Mojo source audit, kernel manifests, kernel fixtures, and readiness reports.
- PSC reporting metric profile with schema-validated derivability classifications, public-data limitations, exclusions, and explicit non-official-reporting caveats.
- PSC sample aggregate reports from event JSONL, including schema validation, warning fields, and `value: null` handling for metrics unavailable from public FYI data.
- Test fixtures and examples for the implemented dependency-light surfaces.

## Experimental or optional

- Mojo/MAX native kernels are preferred where the Modular toolchain is available, but Python fallback semantics remain the compatibility contract.
- FastMCP server support is present as an optional runtime surface and must degrade clearly when FastMCP is unavailable.
- Polars, DuckDB, LanceDB, pySHACL, MAX/OpenAI, and experiment libraries are optional extras and are not required for dependency-light validation. Local/MAX request-pack preparation is repo-local; live model execution remains an external gate.

## Remaining planned roadmap work

- Publication metadata, release package, and methods paper.

## External gates

- Native Mojo release certification requires `pixi run mojo-format-check`, `pixi run mojo-test`, and `pixi run mojo-build` with the Modular toolchain available.
- Live MAX endpoint calls, downloaded model quality measurement, hosted vector services, and GPU/accelerator-specific runs require local tooling, models, and operator review.
- Live Hugging Face/archive pulls require network access, source availability, and any required credentials or terms compliance.
- NZ Legislation/Ombudsman source retrieval requires live source access and source-version capture.
- Registry or dataset publication requires the relevant service credentials and manual release approval.
