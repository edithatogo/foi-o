# Governed re-extraction readiness

## Status

**Blocked at the human target-pin and rights gate.** No re-extraction or
baseline comparison has been run.

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
`fyi-archive/versions/2026-07/backfill_verification.json`. The source checkout
itself remains untouched and dirty on another agent branch.

## Missing governed inputs

1. Human approval or rejection of the candidate raw dataset commit and an
   explicit rights treatment for records whose licence field is null.
2. A real initial ontology-based baseline artifact with immutable revision,
   record identifiers, content digests, and output digest.
3. A real `nlp-policy-nz` extraction pipeline/model revision and runnable
   manifest-to-candidate extraction entry point.
4. A rights-reviewed record selection or heldout sample suitable for processing.

The existing `nlp-policy-nz` NZ adapter bundle cannot satisfy items 2-3. Its
archived evidence explicitly describes the fixture as synthetic and
placeholder-pinned; it uses repeated `a` digests/revisions and no real
source/profile/model pins. Its adapter packages already-produced extraction
records but does not implement a 33,217-record raw-manifest extraction run.

## Required human decision

Approve or reject the candidate Hugging Face commit above. If approved, also
provide or approve the rights rule, baseline artifact, heldout selection, and
immutable `nlp-policy-nz` pipeline/model revision. Until then, no raw records
may be overwritten, no candidate may be promoted, and no empirical comparison
may be claimed.

## Repo-local input audit

The read-only audit contract is implemented in
`src/foi_o_nz/reextraction.py` and
`schemas/json/reextraction-input-audit.schema.json`. Running it against the
verified manifest produced
`examples/v2/reextraction-input-audit.fc27.json`: 33,217 valid content digests,
no duplicate or missing request identifiers, zero declared licences, and
`ready_for_reextraction: false` with blocker `missing_declared_license`.
