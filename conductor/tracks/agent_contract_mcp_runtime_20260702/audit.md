# Agent Contract Audit

Audited at: 2026-07-02T04:55:03Z

## Scope

- `src/foi_o_nz/agent_policy.py`
- `src/foi_o_nz/tool_manifest.py`
- `src/foi_o_nz/openapi.py`
- `src/foi_o_nz/mcp_bundle.py`
- `src/foi_o_nz/mcp_server.py`
- `src/foi_o_nz/replay.py`
- `docs/04-agent-boundaries.md`
- Existing descriptor/runtime tests.

## Current State

- Agent actions carry legal-effect, safety-class, human-certification, and prohibited-follow-on metadata.
- The tool manifest emits policy-derived tools plus additional hand-authored tools.
- OpenAPI and MCP bundle exports contain boundary text, resources, prompts, and tools.
- The optional FastMCP runtime degrades when FastMCP is missing, but its `quality_gate` tool can write an output file when `output_path` is supplied.
- Existing tests check broad boundary presence but do not run a shared descriptor conformance contract across OpenAPI, tool manifest, and MCP bundle.

## Gaps For Phase 1

1. Tool manifest currently duplicates some tools because it emits every `ACTION_POLICY` entry and then appends hand-authored entries with the same names.
2. Descriptor safety metadata is not machine-normalised across tool manifest, MCP bundle, and OpenAPI.
3. There is no reusable guard to reject unsafe descriptor text such as autonomous release, refusal, redaction approval, charging, transfer, extension, complaint/review outcome, or legal certification.
4. Negative unsafe descriptor fixtures are missing.
5. OpenAPI operations have boundary strings but no explicit `x-legal-effect`, `x-read-only`, `x-machine-certification-allowed`, or prohibited-follow-on metadata.

## Deferred To Later Phases

- Runtime FastMCP fixture-mode hardening belongs to Phase 2.
- Guardrail replay integration across policy and descriptors belongs to Phase 3.
- Full optional FastMCP live checks remain an external gate when the dependency is not installed.
