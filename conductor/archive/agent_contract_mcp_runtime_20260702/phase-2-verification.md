# Phase 2 Verification: Runtime Prototype

Date: 2026-07-02

## Scope

Phase 2 hardened the optional FastMCP runtime into a read-only prototype with
fixture-root constrained validation, fail-closed degraded mode, committed schema
resources, bounded prompt context, and live descriptor coverage.

Changed implementation surfaces:

- `src/foi_o_nz/mcp_server.py`
- `tests/test_mcp_runtime.py`
- `README.md`

## Automated Verification

Passed:

```bash
uv run pytest -q tests/test_mcp_runtime.py tests/test_agent_descriptors.py tests/test_table_oci_mcp_bundle.py tests/test_quality.py tests/test_agent_policy.py
```

Result: `20 passed`.

Passed:

```bash
tmpdir=$(mktemp -d)
uv run foi-o-nz export-mcp-bundle --output "$tmpdir/mcp-bundle.json"
uv run foi-o-nz export-tool-manifest --output "$tmpdir/tool-manifest.json"
uv run foi-o-nz export-openapi --output "$tmpdir/openapi.json"
```

Result: MCP bundle, tool manifest, and OpenAPI exports returned `ok`.

Passed:

```bash
uv run python - <<'PY'
from foi_o_nz.mcp_server import create_server, mcp_runtime_status
print(mcp_runtime_status())
create_server()
PY
```

Result: FastMCP was available locally, `mcp_runtime_status()` returned
`mode=fastmcp`, and `create_server()` constructed the runtime.

Passed:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Result: examples ok, repository validation ok, Ruff check passed, and
`96 files already formatted`.

## Conductor Review

`conductor-review` is not installed on PATH in this workspace, so the review was
performed using the `conductor-review` skill protocol as a manual fallback.

Review inputs:

- `conductor/tracks/agent_contract_mcp_runtime_20260702/spec.md`
- `conductor/tracks/agent_contract_mcp_runtime_20260702/plan.md`
- `conductor/workflow.md`
- Phase diff from checkpoint `e9942e7`
- Focused runtime, descriptor, example, repo, export, FastMCP construction, and
  style checks

Findings applied:

- Stable prompt naming was missing from the real FastMCP descriptor surface.
  The prompt now registers as `state_mapping_context`.
- The parameterised schema endpoint is exposed by FastMCP as a resource template,
  so live descriptor coverage now checks `list_resource_templates()`.

Unresolved findings: none.

## Runtime Boundaries Verified

- Missing FastMCP reports degraded mode and `create_server()` fails closed.
- Runtime tools return `read_only: true` and `legal_effect: none`.
- Runtime descriptor metadata sets `machine_certification_allowed: false`.
- `quality_gate` no longer accepts or writes an `output_path`.
- Validation tools resolve inputs inside the configured fixture root.
- Schema resources are limited to committed `schemas/json/*.schema.json` files.
- Live FastMCP tools, prompts, and resource templates expose safe metadata.

## Manual Verification Steps

Autonomous verification substituted for an interactive pause because the user
explicitly requested comprehensive automatic execution.

Maintainer replay:

1. Run the runtime/descriptor tests:
   `uv run pytest -q tests/test_mcp_runtime.py tests/test_agent_descriptors.py`
2. Export the static bundle and contracts:
   `uv run foi-o-nz export-mcp-bundle --output data/processed/mcp-bundle.json`
   and `uv run foi-o-nz export-openapi --output data/processed/openapi.json`
3. Check optional runtime status:
   `uv run python -c "from foi_o_nz.mcp_server import mcp_runtime_status; print(mcp_runtime_status())"`
4. Start the server when FastMCP is installed:
   `uv run foi-o-nz mcp-server`

Expected outcome: the server exposes only read-only preparatory tools/resources
and no release, refusal, redaction, charging, transfer, extension, complaint, or
review outcome certification capability.

## External Gates

- Long-running MCP transport behavior remains operator-run; this phase verifies
  construction, descriptors, helper behavior, and command exports locally.
- Native `conductor-review` command: unavailable locally; manual skill-protocol
  review completed.
