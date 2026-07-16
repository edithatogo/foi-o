# Governed re-extraction readiness

## Status

**Blocked at rights, upstream execution-contract, and empirical human gates.**
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
- `nlp-policy-nz` revision `4150ac35a2a3fba6e8cff0136ca1fc1c109192e4`
  contains an adapter, comparison functions, and a two-record bounded
  evaluation. The bounded input is synthetic, uses placeholder archive pins,
  has no real model pin, and starts from already-produced extraction records
  rather than a raw archive manifest.
- The upstream fixture declares extraction contract `2.0.0`, while this
  repository publishes candidate contract `foi-o-extraction-contract/0.1.0`.
  No compatibility evidence bridges those versions, so the audit fails closed.

## Missing governed inputs

1. An explicit human-approved rights treatment for records whose licence field
   is null.
2. A real initial ontology-based baseline artifact with immutable revision,
   record identifiers, content digests, and output digest.
3. A real `nlp-policy-nz` pipeline/model pin, a runnable manifest-to-candidate
   extraction entry point, and explicit compatibility with candidate contract
   `0.1.0`.
4. A rights-reviewed record selection or heldout sample suitable for processing.

The existing `nlp-policy-nz` NZ adapter bundle cannot satisfy items 2-3. Its
archived evidence explicitly describes the fixture as synthetic and
placeholder-pinned; it uses repeated `a` digests/revisions and no real
source/profile/model pins. Its adapter packages already-produced extraction
records but does not implement a 33,217-record raw-manifest extraction run.

## Required human decision

Approve the rights rule, baseline artifact, heldout selection, contract
alignment, and immutable `nlp-policy-nz` pipeline/model revision. Until then,
no raw records may be overwritten, no candidate may be promoted, and no
empirical comparison may be claimed.

## Repo-local input audit

The read-only audit contract is implemented in
`src/foi_o_nz/reextraction.py` and
`schemas/json/reextraction-input-audit.schema.json`. Running it against the
verified manifest produced
`examples/v2/reextraction-input-audit.fc27.json`: 33,217 valid content digests,
no duplicate or missing request identifiers, zero declared licences, and
`ready_for_reextraction: false` with blocker `missing_declared_license`.
