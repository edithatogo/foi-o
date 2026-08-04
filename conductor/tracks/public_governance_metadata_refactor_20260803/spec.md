# Public governance-metadata refactor specification

## Overview

Separate reusable public governance contracts from case-specific approvals,
request identifiers, local paths, source-content metadata, and execution
receipts. The refactor must preserve historical evidence bytes and compatibility
while making future public-safe candidates mechanically selectable.

## Authoritative inputs

- `conductor/tracks/remaining_evidence_and_release_gates_20260803/release-scope-and-licensing-approval-2026-08-03.md`
  (SHA-256 `6e2a10176bf8daa4b853d18911ab7fcd665228a53f214ce6aee109a760156e59`)
- `LICENSE.md`
- `schemas/json/release-manifest.schema.json`
- `scripts/build_release_manifest.py`
- Existing immutable evidence and approval pins; these remain historical
  records and must not be rewritten.

## Requirements

1. Inventory public contracts that embed exact approvals, request identifiers,
   absolute local paths, credentials, restricted source metadata, or receipts.
2. Define generic, versioned governance configuration and provenance-reference
   contracts that carry opaque pins instead of case-specific content.
3. Add positive and negative fixtures for the public/private boundary.
4. Migrate reusable runtime and schema consumers without changing historical
   evidence bytes or treating derived metadata as source rights.
5. Add deterministic public-safe selection and fail-closed validation.
6. Maintain Markdown/Mermaid and BPMN 2.0 workflow parity.

## Acceptance criteria

- A machine-readable inventory classifies each finding and its controlling
  migration disposition.
- Generic contracts reject local absolute paths, raw approval prose,
  credentials, source content, and direct case identifiers.
- Compatibility tests prove historical pinned artifacts remain verifiable.
- The semantic-core release manifest remains independent of this tranche.
- Full repository and Conductor validation pass.

## Non-functional constraints

- Deterministic, versioned, append-only provenance.
- No destructive rewrite of historical artifacts or Git history.
- No network access or external mutation is required.
- Repository-owned code and schemas use MIT; repository-owned documentation,
  ontology, vocabularies, and mappings use CC BY 4.0.

## External gates

Push, merge, tag, release, publication, upload, redistribution, profile
promotion, and legal certification remain unauthorized and out of scope.

## Out of scope

- Publishing any refactored bundle.
- Moving authentic source content into the repository.
- Reinterpreting historical approvals or rights dispositions.
- Changing empirical memberships, maturity decisions, or legal conclusions.
