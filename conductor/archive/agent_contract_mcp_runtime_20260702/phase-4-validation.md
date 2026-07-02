# Phase 4 Validation: Agent Contract Closeout

Date: 2026-07-02

## Scope

This validation covers the Track 6 agent contract and MCP runtime closeout
before final review and archive.

## Commands

Passed:

```bash
uv run pytest -q
```

Result: `135 passed`.

Passed:

```bash
uv run pytest -q tests/test_agent_policy.py tests/test_agent_descriptors.py tests/test_mcp_runtime.py tests/test_guardrail_replay_agent_contract.py tests/test_table_oci_mcp_bundle.py
```

Result: `18 passed`.

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
uv run foi-o-nz schema-drift
```

Result: examples ok, repository validation ok, and schema drift returned
`ok: true` with warning-level pre-existing top-level drift for unrelated
`core-event`, `reporting-metric`, and `request-profile` schemas.

Passed:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Result: Ruff check passed and `97 files already formatted`.

## External Gates

- Optional FastMCP was installed and the runtime construction path was verified.
- Long-running MCP transport behavior remains operator-run.
- Native `conductor-review` command remains unavailable locally and will be
  covered by manual skill-protocol fallback in the next closeout task.
