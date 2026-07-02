# Specification: Agent contract and MCP runtime hardening

## Objective

Promote the experimental MCP/tool contract into a hardened read-only prototype with descriptor conformance tests and unsafe-tool guards.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/16
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Harden the read-only MCP/resources/tools/prompts contract for state mapping, validation, quality checks, and bounded context assembly.
- Add descriptor conformance tests for OpenAPI, tool manifest, MCP bundle, and live FastMCP server descriptors.
- Reject or flag unsafe tool descriptions and any capability that could certify legal outcomes.
- Preserve deterministic fallback behavior when FastMCP is unavailable.

## Acceptance Criteria

- MCP/tool descriptor tests validate safe capabilities and reject unsafe examples.
- The prototype server can run over fixture data or explicitly fail closed when optional dependencies are absent.
- Documentation gives exact server, bundle, and conformance commands.
- No tool can certify release, refusal, redaction, charging, transfer, extension, or complaint/review outcomes.
