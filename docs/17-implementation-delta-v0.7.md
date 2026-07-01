# Implementation delta v0.7 — Mojo-first, Python fallback made explicit

This pass shifts the architecture from "Mojo present as experimental kernels" to
"Mojo preferred where available, Python fallback as a tested compatibility
contract".

## Added

- `src/foi_o_nz/kernel_fallback.py`: dependency-light reference semantics for
  deterministic kernels.
- `src/foi_o_nz/native_kernel.py`: native-kernel discovery, status reports,
  operation evaluation, and conformance reporting.
- CLI commands:
  - `foi-o-nz kernel-status`
  - `foi-o-nz kernel-eval`
  - `foi-o-nz kernel-conformance`
- JSON Schemas:
  - `native-kernel-status.schema.json`
  - `kernel-conformance.schema.json`
- Mojo modules:
  - `transition.mojo`
  - `hash.mojo`
  - `redaction.mojo`
- Mojo tests:
  - `test_transition.mojo`
  - `test_hash.mojo`
  - `test_redaction.mojo`
- OpenAPI/tool-manifest/MCP planning bundle entries for kernel introspection and
  conformance.

## Design stance

Mojo is now the preferred deterministic-kernel target for small hot-path logic,
while Python remains the fallback/control plane. The Python fallback does not
certify legal outcomes and is not a policy fork; it is the executable contract
that native Mojo implementations must match.

## Still deliberately not moved into Mojo

- JSON Schema validation
- RDF/SHACL validation
- Polars/DuckDB/LanceDB data materialisation
- FastMCP runtime
- large file ingestion and Parquet/Arrow writes

Those remain in Python or mature data engines until the Mojo-native ecosystem is
ready to carry them safely.
