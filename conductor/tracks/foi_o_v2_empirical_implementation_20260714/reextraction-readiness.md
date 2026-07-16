# Governed re-extraction readiness

## Status

**Blocked at rights, source-evidence, and empirical human gates.**
The candidate target revision is approved for repo-local preparation only. No
re-extraction or baseline comparison has been run.

## Verified candidate raw input

- Dataset: `edithatogo/fyi-archive-nz`
- Hugging Face commit: `fc27bfa471c598a31d975cfa2b603b1a11408e55`
- Configuration and split: `default` / `requests`
- Manifest: `manifests/latest_manifest.json` at that exact commit
- Manifest SHA-256:
  `23cab9ee0ac6986326d67c91a91e415456a1d0589c90ec1c1628556e0d0d6e1e`
- Manifest records: `33,217`
- Manifest metadata: `fyi_cli_version=1.2.0`, archive schema version `0.10.3`,
  generated `2026-07-13T01:57:41.585256+00:00`
- Integrity check: all `33,217` records carry a non-empty `content_sha256`.
- Rights check: all `33,217` records have `license: null`; no record-level
  redistribution approval can be inferred from this field.

The Hugging Face dataset API returned the commit as the dataset SHA and the
downloaded JSON manifest reproduced the SHA-256 already recorded in
`fyi-archive/versions/2026-07/backfill_verification.json`. The separate source
checkout itself remains untouched.

## Verified upstream implementation state

The schema-backed audit at
`examples/v2/upstream-extraction-readiness.2026-07-16.json` pins two read-only
upstream inspections:

- `fyi-archive` revision `7e405aae53d726cb9214218bd83c5b7796d781a7`
  commits attachment-aware capture and retains a July verification report for
  33,217 merged and published records. This verifies archive orchestration; it
  does not cure the null record-level licence metadata in the pinned manifest.
- `nlp-policy-nz` revision `ee3fb0b4b686f565f4ba18856a2bda4284466328`
  enforces extraction contract `0.1.0`, provides the fail-closed
  `foio-extract-manifest` entry point, and pins
  `nlpaueb/legal-bert-base-uncased` to immutable repository and weights
  digests. Its deterministic lexical candidate pass does not apply the model,
  so no model-derived result is claimed. The retained two-record bounded input
  remains synthetic and placeholder-pinned.
- Contract alignment, the raw-manifest entry point, and a real model pin are
  therefore verified. The pinned 33,217-record archive manifest still does not
  provide inline content or content paths required by the entry point.

## Missing governed inputs

1. An explicit human-approved rights treatment for records whose licence field
   is null.
2. A real initial ontology-based baseline artifact with immutable revision,
   record identifiers, content digests, and output digest.
3. A content-bearing, immutable input manifest suitable for the verified
   `nlp-policy-nz` manifest-to-candidate entry point.
4. A rights-reviewed record selection or heldout sample suitable for processing.

The verified `nlp-policy-nz` consumer resolves the earlier contract, entry-point,
and model-pin blockers but cannot supply missing source rights or raw content.
Its archived bounded evidence remains synthetic and placeholder-pinned, and no
33,217-record extraction run or empirical comparison has been performed.

## Required human decision

Approve the rights rule, content-bearing heldout selection, and baseline
artifact, then complete independent annotation and adjudication. Until then, no
raw records may be overwritten, no candidate may be promoted, and no empirical
comparison may be claimed.

## Repo-local input audit

The read-only audit contract is implemented in
`src/foi_o_nz/reextraction.py` and
`schemas/json/reextraction-input-audit.schema.json`. Running it against the
verified manifest produced
`examples/v2/reextraction-input-audit.fc27.json`: 33,217 valid content digests,
no duplicate or missing request identifiers, zero declared licences, and
`ready_for_reextraction: false` with blocker `missing_declared_license`.
