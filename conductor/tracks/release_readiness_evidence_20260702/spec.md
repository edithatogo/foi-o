# Specification: Harden release-readiness evidence and kernel fallback validation

## Objective

Make FOI-O NZ release-readiness claims easier to verify by tightening repo-local evidence around validation commands, kernel fallback contracts, and documentation status.

## Background

The repository already contains a broad v0.8 surface: Python validation and analytics utilities, JSON Schemas, RDF/SHACL artifacts, deterministic retrieval/redaction/risk utilities, agent contracts, MCP bundle scaffolding, and experimental Mojo/MAX kernels with Python fallback behavior. The next maintenance slice should make it harder for release notes or readiness reports to outrun executable evidence.

## Scope

- Audit existing release/readiness/status documents for claims that should be backed by commands, tests, schemas, examples, or manifests.
- Add or strengthen tests that prove Python fallback behavior remains available when native Mojo/MAX surfaces are missing or unavailable.
- Ensure validation commands for examples, schemas, quality gates, and kernel manifests are documented in a repeatable location.
- Update status documentation so implemented, experimental, planned, and blocked surfaces are clearly separated.

## Out of Scope

- Building new autonomous OIA decision functionality.
- Expanding the FYI archive corpus or storing generated data payloads in Git.
- Replacing human certification boundaries with automated legal determinations.
- Reworking the repository architecture or package layout.

## Acceptance Criteria

- A maintainer can identify the exact command set for release-readiness validation.
- Kernel fallback expectations are covered by tests or static manifests.
- Documentation distinguishes implemented, experimental, and planned features without overstating readiness.
- Human certification boundaries remain unchanged and visible.
- All relevant Python quality checks and available Mojo checks pass, or any unavailable external tool is explicitly documented as an external gate.
