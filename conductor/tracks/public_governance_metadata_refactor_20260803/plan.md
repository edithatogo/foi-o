# Implementation plan

## Phase 1: Inventory and contract boundary

- [x] Preserve the v0.1 analyst packet's historical licence-placeholder pin
      independently of the current repository rights notice. (`bb51633`)
- [x] Inventory case-specific governance metadata in public-candidate paths and
      classify each item by sensitivity, ownership, and migration disposition.
      (Inventory: `governance-metadata-inventory.json`)
- [x] Add failing positive and negative fixtures for generic public governance
      and provenance-reference contracts. Covered in
      `tests/test_generic_governance_contracts.py` and `examples/v2/`.
- [x] Implement the versioned generic contracts and fail-closed validators.
      Implemented in `schemas/json/generic-governance-metadata.schema.json`,
      `schemas/json/provenance-reference.schema.json`, and
      `src/foi_o_nz/generic_governance.py`.
- [x] Run focused tests and automated phase review. (Review:
      `phase-1-review-2026-08-30.md`)

## Phase 2: Compatibility-preserving migration

- [x] Migrate reusable consumers to opaque, hash-pinned references while
      preserving historical evidence bytes. (Implemented in
      `src/foi_o_nz/generic_governance.py`)
- [x] Add compatibility tests for earlier analyses, manifests, and approvals.
      (Covered in `tests/test_governance_migration_compatibility.py`)
- [x] Add deterministic public-safe selection checks. (Implemented
      `is_public_safe_manifest` and covered in
      `tests/test_governance_migration_compatibility.py`)
- [x] Run focused tests and automated phase review. (Review:
      `phase-2-review-2026-08-30.md`)

## Phase 3: Validation and closeout

- [x] Synchronize Markdown/Mermaid and BPMN 2.0 workflow documentation.
      (`workflow.md`, `workflow.bpmn`)
- [x] Run full repository and Conductor validation.
- [x] Record residual external gates and complete whole-track review. (Review:
      `track-review-2026-08-30.md`)
- [x] Archive only when all repository-owned acceptance criteria are satisfied.
