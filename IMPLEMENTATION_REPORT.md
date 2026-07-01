# FOI-O NZ implementation report

Generated for the July 2026 scaffold handoff.

## Implemented surfaces

- Standalone repository scaffold for `edithatogo/foi-o-nz`.
- Python package `foi_o_nz` with CLI, Pydantic models, JSON Schema validation,
  FYI manifest normalisation, state mapping, analytics summaries, quality gates,
  RDF export, optional DuckDB materialisation, and run-manifest provenance.
- Experimental Mojo package with deterministic state/certification kernels and
  machine working-day helpers.
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

## Locally verified in this environment

```text
python -m compileall -q src tests scripts
PYTHONPATH=src python -m pytest -q
25 passed

PYTHONPATH=src python -m foi_o_nz.cli smoke-fixture -o /tmp/foio-smoke
PYTHONPATH=src python -m foi_o_nz.cli normalise-manifest ...
PYTHONPATH=src python -m foi_o_nz.cli validate-jsonl ...
PYTHONPATH=src python -m foi_o_nz.cli quality-gate ...
PYTHONPATH=src python -m foi_o_nz.cli export-rdf ...
PYTHONPATH=src python -m foi_o_nz.cli clock 2026-12-23
PYTHONPATH=src python -m foi_o_nz.cli validate-repo
```

## Not locally verified

The sandbox does not include the Modular Mojo/MAX toolchain, so Mojo formatting,
Mojo native tests, and Mojo binary build remain CI/operator checks after Pixi
installs the Modular packages.

## Design boundary

The implementation keeps the GoogleAI/Mojo notes as a strategic direction, not a
source of truth. Mojo/MAX is used for deterministic kernels and future hot paths;
Polars/DuckDB/LanceDB remain the pragmatic data layer for ingestion and analysis
until Mojo-native dataframe/Arrow tooling is demonstrably production-ready.
