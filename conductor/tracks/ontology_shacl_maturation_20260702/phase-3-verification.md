# Phase 3 Verification: Semantic Export Consistency

Date: 2026-07-02

## Scope

- RDF export uses ontology/SKOS identifier URIs for event type, assertion status, and lifecycle state.
- Croissant-style dataset metadata advertises FOIO, DCAT, and ODRL context terms and FOIO publication semantics.
- Portable graph export includes `semantic_type` and event-type URI hints.
- Semantic alignment documentation records expected validation commands.

## Verification Commands

- `uv run pytest -q tests/test_rdf_export.py tests/test_ledger_chunks_risk_metadata.py tests/test_review_advice_graph_attestation_gold_annotation.py tests/test_semantic_alignment.py tests/test_shacl_safety_profiles.py tests/test_request_profile_jsonld.py`
  - Result: `28 passed`.
- `uv run ruff check src tests scripts`
  - Result: passed.
- `uv run ruff format --check src tests scripts`
  - Result: `104 files already formatted`.
- `uv run python scripts/validate_examples.py`
  - Result: `examples ok`.
- `uv run foi-o-nz validate-repo`
  - Result: `repository validation ok`.
- `uv run foi-o-nz schema-drift`
  - Result: ok with warning-only top-level schema drift for `core-event.schema.json`, `reporting-metric.schema.json`, and `request-profile.schema.json`.
- `git diff --check`
  - Result: passed.

## Conductor Review

The `conductor-review` executable was not available in this environment. Manual review fallback checked RDF, metadata, graph-export, docs, and tests in the Phase 3 diff. No high-confidence Phase 3 fixes remained after verification.

## Risks and External Gates

- RDF semantic fields now prefer identifier URIs. Consumers that previously expected literal labels should resolve labels from the SKOS vocabularies.
- External publication registry validation remains outside repo-local export consistency checks.
