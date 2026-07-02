# Implementation delta v0.2

This note records the second implementation pass after the initial standalone
repo scaffold.

## Added

- `foi_o_nz.dates`: indicative OIA/LGOIMA clock helpers with working-day
  addition, optional OIA summer exclusion, and explicit warning strings.
- `foi_o_nz.extractors`: conservative rule-based correspondence extraction for
  `MessageObserved` and candidate process events.
- `foi_o_nz.quality`: event-stream quality gates for evidence and human
  certification boundaries.
- `foi_o_nz.rdf_export`: RDF/Turtle export for request profiles and core events.
- `foi_o_nz.duckdb_export`: optional DuckDB materialisation and portable SQL
  bootstrap output.
- `foi_o_nz.manifest`: file checksums and run-manifest provenance records.
- JSONL validation command and run-manifest JSON Schema.
- Additional Mojo clock kernel and native test stub.

## CLI additions

```bash
foi-o-nz validate-jsonl EVENTS.jsonl --schema schemas/json/core-event.schema.json
foi-o-nz quality-gate EVENTS.jsonl --output quality-report.json
foi-o-nz export-rdf --requests-jsonl requests.jsonl --events-jsonl events.jsonl --output foi-o-nz.ttl
foi-o-nz build-duckdb --database foi-o-nz.duckdb --requests-jsonl requests.jsonl --events-jsonl events.jsonl
foi-o-nz write-duckdb-sql --output duckdb-bootstrap.sql
foi-o-nz clock 2026-12-23
foi-o-nz can-transition Received SearchPlanning
```

## Boundary retained

Rule extractors may emit candidate `DecisionCommunicated`, `ReleaseMade`,
`RefusalCommunicated`, and `ChargeNoticeSent` events, but those events are
marked as requiring human certification and carry no positive certification.
They are process signals for review, not final decisions.

## Process-rule quality examples

Passing quality output can still include warning findings. For example, a
candidate `ReleaseMade` event with evidence, `requires_human_certification:
true`, and `human_certification.certified: false` is metadata-valid, but if its
legal reference lacks `version_id`, `retrieved_at`, `source_status`, or
`applicability_basis`, the gate emits `unversioned_legal_reference`.

When a source is marked `external_gate`, `deprecated`, or `unknown`, the gate
also emits `stale_or_unverified_legal_reference`. These warnings do not make the
event legally wrong; they mean the repo-local proof is insufficient for legal
certainty.

Failing quality output remains reserved for boundary violations such as missing
evidence, missing human-certification metadata on dispositive events, or a
`certified` assertion without positive human certification.
