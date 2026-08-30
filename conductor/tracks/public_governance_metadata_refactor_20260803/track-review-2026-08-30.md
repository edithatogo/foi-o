# Track Review: Public Governance-Metadata Refactor

- **Track:** `public_governance_metadata_refactor_20260803`
- **Review Date:** 2026-08-30
- **Status:** PASS (Repository-owned acceptance criteria satisfied)

## Executive Summary

This track refactors case-specific metadata out of generic governance and release contracts,
establishing generic public schema contracts, opaque provenance reference pins, and fail-closed
public-safety validators while preserving all historical evidence bytes and earlier candidate compatibility.

## Acceptance Criteria Verification

| Requirement | Evidence / Location | Result |
|---|---|---|
| Historical licence placeholder preserved | `bb51633` | PASS |
| Governance metadata inventory & classification | `governance-metadata-inventory.json` (162 items across 91 files) | PASS |
| Generic governance JSON Schema | `schemas/json/generic-governance-metadata.schema.json` | PASS |
| Provenance reference JSON Schema | `schemas/json/provenance-reference.schema.json` | PASS |
| Fail-closed Python validators | `src/foi_o_nz/generic_governance.py` | PASS |
| Public/private boundary fixtures | `examples/v2/schema-valid/`, `examples/v2/schema-invalid/` | PASS |
| Deterministic public-safe selection checks | `is_public_safe_manifest` in `src/foi_o_nz/generic_governance.py` | PASS |
| Compatibility tests | `tests/test_governance_migration_compatibility.py` | PASS |
| Paired workflow documentation | `workflow.md`, `workflow.bpmn` | PASS |

## Residual External Gates

- **External Publication Gate:** Live publication or deposit to external destinations remains governed by declared human gates. This track satisfies all repository-owned contract refactoring and validation prerequisites.
