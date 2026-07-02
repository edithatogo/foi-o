# Implementation status

This status page separates implemented repo-local surfaces, experimental optional surfaces, planned roadmap work, and external gates. It supersedes the older v0.1-only status snapshot.

## Implemented and repo-local

- Python package `foi_o_nz` with Typer CLI entry points.
- Pydantic models and JSON Schemas for core events, request profiles, agent actions, reporting metrics, review tasks, manifests, kernel reports, and related records.
- FYI/Alaveteli state mapping, JSON/JSONL manifest normalisation, event analytics, transition audit, quality gates, and schema validation helpers.
- RDF/Turtle export, JSON-LD context export, SHACL parse/degraded-mode wrapper, ontology seed, SKOS vocabularies, and SHACL shapes.
- Deterministic embeddings, chunking, lexical/vector-style retrieval, redaction candidates, risk scans, stream diffs, agent packs, ledgers, reproducibility manifests, CAS, lineage, traces, review queues, process advice, annotation tasks, graph export, table contracts, OCI layout summaries, attestations, and MCP bundle scaffolds.
- Python fallback kernel contract, native-kernel discovery/status reports, conformance reports, static Mojo source audit, kernel manifests, kernel fixtures, and readiness reports.
- PSC reporting metric profile with schema-validated derivability classifications, public-data limitations, exclusions, and explicit non-official-reporting caveats.
- Test fixtures and examples for the implemented dependency-light surfaces.

## Experimental or optional

- Mojo/MAX native kernels are preferred where the Modular toolchain is available, but Python fallback semantics remain the compatibility contract.
- FastMCP server support is present as an optional runtime surface and must degrade clearly when FastMCP is unavailable.
- Polars, DuckDB, LanceDB, pySHACL, MAX/OpenAI, and experiment libraries are optional extras and are not required for dependency-light validation.

## Planned roadmap work

- Live or fixture-backed corpus-profile workflow with a 100-request goldset.
- Hardened event extraction timelines and evaluation fixtures.
- Official NZ holiday/closure calendar support and source-versioned legal/guidance references.
- PSC sample aggregate reports and publication-safe reporting documentation.
- Hardened read-only MCP runtime contract and unsafe-tool descriptor tests.
- Bounded MAX/local extraction and LanceDB semantic retrieval with deterministic fallback.
- Ontology/SHACL maturation and standards alignment.
- Publication metadata, release package, and methods paper.

## External gates

- Native Mojo release certification requires `pixi run mojo-format-check`, `pixi run mojo-test`, and `pixi run mojo-build` with the Modular toolchain available.
- Live Hugging Face/archive pulls require network access, source availability, and any required credentials or terms compliance.
- NZ Legislation/Ombudsman source retrieval requires live source access and source-version capture.
- Registry or dataset publication requires the relevant service credentials and manual release approval.
