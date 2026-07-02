# Plan: Agent contract and MCP runtime hardening

## Phase 1: Descriptor Contract [checkpoint: e9942e7]

- [x] Task: Audit current agent contracts (`aa94872`)
    - [x] Review agent policy, tool manifest, OpenAPI export, MCP bundle, MCP server, and docs.
    - [x] Identify descriptor drift and unsafe-capability gaps.
- [x] Task: Write descriptor conformance tests (`83db169`)
    - [x] Validate OpenAPI/tool-manifest/MCP-bundle descriptors for safe read-only semantics.
    - [x] Add negative fixtures for unsafe certification-capable tool descriptions.
- [x] Task: Implement descriptor hardening (`f375422`)
    - [x] Update descriptors and exports to make non-dispositive boundaries machine-checkable.
    - [x] Ensure unsafe examples fail tests and safe examples remain stable.
- [x] Task: Conductor - User Manual Verification 'Descriptor Contract' (Protocol in workflow.md) (`e9942e7`)

## Phase 2: Runtime Prototype [checkpoint: be3aae6]

- [x] Task: Write MCP runtime tests (`d4878f0`)
    - [x] Cover fixture-backed state mapping, validation, quality gate, and context/resource behaviors.
    - [x] Cover missing FastMCP dependency with explicit degraded-mode messaging.
- [x] Task: Implement MCP runtime hardening (`ab36781`)
    - [x] Refine server startup, tool registration, and error handling for read-only fixture mode.
    - [x] Keep all write, certify, release, refusal, redaction, and charge operations absent.
- [x] Task: Conductor - User Manual Verification 'Runtime Prototype' (Protocol in workflow.md) (`be3aae6`)

## Phase 3: Agent Guardrail Replay [checkpoint: 4819102]

- [x] Task: Write guardrail replay tests for tool contracts (`c4fb82e`)
    - [ ] Verify unsafe agent actions are blocked or routed to human review.
    - [ ] Verify safe preparatory actions retain provenance and warnings.
- [x] Task: Implement guardrail replay integration (`a94977b`)
    - [x] Connect policy, replay, and descriptor checks where gaps are found.
    - [x] Update docs with operator-facing safety checks.
- [x] Task: Conductor - User Manual Verification 'Agent Guardrail Replay' (Protocol in workflow.md) (`4819102`)

## Phase 4: Agent Contract Closeout

- [x] Task: Run agent contract validation (`fc9517d`)
    - [x] Run agent policy, OpenAPI, tool-manifest, MCP bundle, replay, and server tests.
    - [x] Run optional FastMCP checks if installed or document the external gate.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Agent Contract Closeout' (Protocol in workflow.md)
