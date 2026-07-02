# Plan: Agent contract and MCP runtime hardening

## Phase 1: Descriptor Contract

- [x] Task: Audit current agent contracts (`aa94872`)
    - [x] Review agent policy, tool manifest, OpenAPI export, MCP bundle, MCP server, and docs.
    - [x] Identify descriptor drift and unsafe-capability gaps.
- [x] Task: Write descriptor conformance tests (`83db169`)
    - [x] Validate OpenAPI/tool-manifest/MCP-bundle descriptors for safe read-only semantics.
    - [x] Add negative fixtures for unsafe certification-capable tool descriptions.
- [~] Task: Implement descriptor hardening
    - [ ] Update descriptors and exports to make non-dispositive boundaries machine-checkable.
    - [ ] Ensure unsafe examples fail tests and safe examples remain stable.
- [ ] Task: Conductor - User Manual Verification 'Descriptor Contract' (Protocol in workflow.md)

## Phase 2: Runtime Prototype

- [ ] Task: Write MCP runtime tests
    - [ ] Cover fixture-backed state mapping, validation, quality gate, and context/resource behaviors.
    - [ ] Cover missing FastMCP dependency with explicit degraded-mode messaging.
- [ ] Task: Implement MCP runtime hardening
    - [ ] Refine server startup, tool registration, and error handling for read-only fixture mode.
    - [ ] Keep all write, certify, release, refusal, redaction, and charge operations absent.
- [ ] Task: Conductor - User Manual Verification 'Runtime Prototype' (Protocol in workflow.md)

## Phase 3: Agent Guardrail Replay

- [ ] Task: Write guardrail replay tests for tool contracts
    - [ ] Verify unsafe agent actions are blocked or routed to human review.
    - [ ] Verify safe preparatory actions retain provenance and warnings.
- [ ] Task: Implement guardrail replay integration
    - [ ] Connect policy, replay, and descriptor checks where gaps are found.
    - [ ] Update docs with operator-facing safety checks.
- [ ] Task: Conductor - User Manual Verification 'Agent Guardrail Replay' (Protocol in workflow.md)

## Phase 4: Agent Contract Closeout

- [ ] Task: Run agent contract validation
    - [ ] Run agent policy, OpenAPI, tool-manifest, MCP bundle, replay, and server tests.
    - [ ] Run optional FastMCP checks if installed or document the external gate.
- [ ] Task: Run Conductor review and apply high-confidence fixes
    - [ ] Run `conductor-review` for the track scope.
    - [ ] Apply high-confidence fixes and rerun focused checks.
- [ ] Task: Conductor - User Manual Verification 'Agent Contract Closeout' (Protocol in workflow.md)
