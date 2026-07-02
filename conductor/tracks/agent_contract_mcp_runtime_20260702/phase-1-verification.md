# Phase 1 Verification: Descriptor Contract

Date: 2026-07-02

## Scope

Phase 1 hardened the agent-facing descriptor contract for the OpenAPI export,
tool manifest, MCP bundle, and unsafe descriptor examples.

Changed implementation surfaces:

- `src/foi_o_nz/agent_contract.py`
- `src/foi_o_nz/tool_manifest.py`
- `src/foi_o_nz/openapi.py`
- `src/foi_o_nz/mcp_bundle.py` generated example output
- `tests/test_agent_descriptors.py`
- `examples/mcp-bundle.small.json`

## Automated Verification

Passed:

```bash
uv run pytest -q tests/test_agent_descriptors.py tests/test_tool_manifest_benchmarks.py tests/test_table_oci_mcp_bundle.py tests/test_agent_policy.py tests/test_ledger_chunks_risk_metadata.py
```

Result: `18 passed`.

Passed:

```bash
uv run python scripts/validate_examples.py
```

Result: `examples ok`.

Passed:

```bash
uv run foi-o-nz validate-repo
```

Result: `repository validation ok`.

Passed:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Result: Ruff check passed; `95 files already formatted`.

## Conductor Review

`conductor-review` is not installed on PATH in this workspace, so the review was
performed using the `conductor-review` skill protocol as a manual fallback.

Review inputs:

- `conductor/tracks/agent_contract_mcp_runtime_20260702/spec.md`
- `conductor/tracks/agent_contract_mcp_runtime_20260702/plan.md`
- `conductor/workflow.md`
- Phase diff from `5fc0721` through the phase head
- Focused descriptor, manifest, bundle, policy, example, repo, and style checks

Finding applied:

- Reworded runtime readiness descriptors from ambiguous "release certification"
  language to "release readiness".
- Added `release certification` to unsafe descriptor phrase detection.
- Regenerated the committed MCP bundle example.

Unresolved findings: none.

## Manual Verification Steps

Autonomous verification substituted for an interactive pause because the user
explicitly requested comprehensive automatic execution.

Maintainer replay:

1. Run the descriptor tests:
   `uv run pytest -q tests/test_agent_descriptors.py tests/test_tool_manifest_benchmarks.py tests/test_table_oci_mcp_bundle.py tests/test_agent_policy.py tests/test_ledger_chunks_risk_metadata.py`
2. Regenerate and validate examples:
   `uv run python scripts/validate_examples.py`
3. Validate the repository:
   `uv run foi-o-nz validate-repo`
4. Confirm descriptor reports reject unsafe text:
   `uv run pytest -q tests/test_agent_descriptors.py -k unsafe`

Expected outcome: all commands pass, and no descriptor advertises write,
certification, release/refusal/redaction/charge/extension/transfer, or complaint
outcome authority.

## External Gates

- Native `conductor-review` command: unavailable locally; manual skill-protocol
  review completed.
- Live FastMCP server descriptor checks are intentionally deferred to Phase 2.
