# Specification: FOI-O V2 empirical-governance overlay

## Objective

Integrate the reviewed FOI-O V2 R2 work package into the existing `foi-o-nz`
package as an additive empirical-governance layer. The programme source of truth
remains `edithatogo/rulesandprocesses` track
`foi_o_v2_triangulation_20260708`; this local track owns only repository-native
implementation, tests, migration decisions, and checkpoints.

The conformance, triangulation, fixture-independence, and release-evidence
extensions were adapted from `edithatogo/rac-conformance`. They are recorded as
design provenance and optional interoperability guidance, not an external
runtime dependency or standards claim.

## Requirements

- Preserve the `foi-o-nz` package name and `foi_o_nz` namespace.
- Extend existing event, provenance, annotation, gold-set, legal-source,
  transition-audit, state-mapping, and `oia_rules` surfaces by reference.
- Validate positive and negative fixtures for every empirical contract.
- Keep automated labels, mappings, and rule results non-certified by default.
- Preserve bitemporal source information, source rights, raw platform states,
  uncertainty, conflicts, and unknowns.
- Keep publication, gold promotion, legal certification, and remote actions human-gated.
- Preserve the confirmed `fyi-cli` -> `fyi-archive` -> Hugging Face source path.
- Use `nlp-policy-nz` for ontology-pinned candidate extraction and keep derived
  outputs separate from immutable archive manifests.
- Defer `fe-reader`; it is not an immediate dependency for the V2 re-extraction.
- Version the extraction/profile contract and publish machine-readable
  capabilities, migration behavior, and unsupported surfaces.
- Require independent promotion of extracted candidates and deterministic
  source-triangulation exceptions before gold or legal-mapping claims.
- Produce a release-evidence bundle suitable for updating the deferred
  RaC Conformance papers after the next FOI-O release.

## Acceptance criteria

- ADR and documentation numbering is reconciled with the live repository.
- Schemas, examples, Pydantic models, and public exports pass native checks.
- Existing V0.8/V1 tests continue to pass.
- Import provenance, decisions, risks, outputs, traceability, and gates are recorded.
- No push, issue/PR mutation, release, dataset publication, or legal certification occurs.
- A linked GitHub issue may be created when explicitly authorized by the user.
- Named archive, extraction, FOI-O, and read-only agent consumers pass contract
  tests against the same pinned release evidence.
