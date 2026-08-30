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
- [ ] Run focused tests and automated phase review.

## Phase 2: Compatibility-preserving migration

- [ ] Migrate reusable consumers to opaque, hash-pinned references while
      preserving historical evidence bytes.
- [ ] Add compatibility tests for earlier analyses, manifests, and approvals.
- [ ] Add deterministic public-safe selection checks.
- [ ] Run focused tests and automated phase review.

## Phase 3: Validation and closeout

- [ ] Synchronize Markdown/Mermaid and BPMN 2.0 workflow documentation.
- [ ] Run full repository and Conductor validation.
- [ ] Record residual external gates and complete whole-track review.
- [ ] Archive only when all repository-owned acceptance criteria are satisfied.
