# AU-CTH fresh-holdout rights and freeze plan

> Scope boundary: the previously approved AU-CTH mature profile remains
> bounded to its pinned 100-unit holdout. This plan concerns only a separate
> fresh-holdout maturity decision and must not overwrite or broaden the prior
> decision. See `docs/94-au-cth-maturity-scope-reconciliation-2026-08-03.md`.

## Historical non-freezeable evidence

The original AU-CTH candidate inventory is retained for provenance but is not
freezeable:

- Internet Archive CDX scope: `www.righttoknow.org.au/request/*`.
- Filters: successful HTML captures, digest collapse.
- Retrieved rows: 10,000, reaching the configured bound.
- Reported pages: 27; complete pagination is not established.
- Canonical request URLs: 224; calibration URLs excluded: 4; additional
  candidate URLs in the bounded ledger: 217.
- CDX export SHA-256:
  `e9560805c2ae6ab97baa46a211afebb408f89da5b366551c142df8e11d9a42c0`.
- Candidate ledger SHA-256:
  `bc85e404d28f0aff8615c6cd7f8058491e847c6e08a40cc4f2c3650091dd484c`.

The associated legacy candidate records are
`examples/v2/au-cth-fresh-holdout-coverage.pending.json` and
`examples/v2/au-cth-fresh-holdout-source-approval.pending.json`. They describe
the bounded 10,000-row retrieval above and must not be treated as current
population, rights, or frame evidence. Their historical hashes and contents
remain unchanged.

## Reconciled complete metadata evidence

The exact-scope completion produced and subsequent restricted-local
verification confirmed the complete Internet Archive CDX metadata artifact:
26 pages, 26,000 records, CDX SHA-256
`954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`, and
verified retrieval-evidence SHA-256
`0795be14775616416f61fb4131c397e7f2496f72c9fc534a357a98ec6e827331`.
These are the controlling metadata pins for any new AU-CTH fresh-frame
candidate. The earlier retrieval-evidence value
`b6dc23e32048b1ef252b2157080280d7e411870d0fe0f4ca181ca8a4e8160d64`
is preserved here only as a superseded historical report and must not be used
to freeze a frame.

The complete CDX artifact resolves pagination completeness for metadata only.
It is not itself a source population and does not establish authority identity,
rights, accessible text, duplicate-cluster exclusions, or empirical-frame
eligibility. Any new candidate must be derived from the complete 26,000-record
artifact and independently pinned retained replay/classification evidence; it
must not extend or mutate the legacy 10,000-row candidates.

## Local readiness result — 2026-08-03

Repository-local preparation is complete for the reconciled metadata evidence:

- The complete 26,000-record CDX hash and verified retrieval-evidence hash are
  recorded above and supersede the legacy candidate's metadata basis.
- The four calibration URLs and their cluster-exclusion rule remain pinned to
  source-population SHA-256
  `2d797390fcdb84fbb362e6fccb03131e77247f553da12ed28de2ddaa4fc9ced8`.
- The legacy 10,000-row candidate artifacts remain pending, non-freezeable,
  and ineligible for promotion to a frame.
- No live-origin access, attachment retrieval, link traversal, or new replay
  was performed by this update.

The retained replay/classification artifacts were subsequently located. The
older replay-summary contract is now handled by a compatibility validator, but
the exact nine-record failure ledger remains unrecovered and unverified at the
retained manifest root. See
`docs/95-au-cth-replay-ledger-recovery-outcome-2026-08-03.md`. The retained
artifacts therefore remain candidate evidence only and do not support frame
approval until the ledger is recovered or a provenance-complete replacement is
approved and the resulting evidence chain is revalidated.

## Options

### Option A — reconcile the completed population and validate records (recommended)

Use the verified 26,000-record CDX artifact as the sole metadata parent. Recover
the exact nine-record ledger or obtain approval for a provenance-complete
replacement, revalidate the retained replay/classification chain, select
canonical request URLs, exclude the four calibration URLs and every duplicate
cluster containing one, then validate the selected retained HTML artifacts.
Record rights/accessibility disposition per candidate before preparing a freeze
packet.

Rationale: this provides the strongest evidence that the holdout frame is
complete within its declared scope and avoids treating the legacy 10,000-row
truncation as a population frame. It requires no further CDX pagination.

### Option B — use the retained 517-record AU-CTH HTML subset as a bounded fallback

Re-validate the already retained 517-record candidate, prove that every prior
calibration unit and duplicate cluster is excluded, and create a fresh frame
only for the remaining rights-eligible text units. This requires a new exact
source/frame approval because it changes the proposed population and may not
support the preregistered independent design.

Rationale: it avoids new replay, but it is weaker than Option A and may produce
an insufficient or non-independent holdout.

### Option C — stop the AU-CTH remediation track at candidate status

Retain the calibration result and incomplete candidate inventory as evidence,
without freezing, sampling, annotating, or promoting.

Rationale: this is the correct outcome if rights, pagination, or accessible
text cannot be established.

## Recommended dependency sequence

1. Pin the complete 26-page, 26,000-record CDX artifact and verified retrieval
   evidence recorded above; do not reuse the legacy 10,000-row candidate as a
   frame parent.
2. Recover the exact nine-record failure ledger or obtain approval for a
   provenance-complete replacement, then revalidate the retained manifest and
   replay/classification chain.
3. Build a canonical URL ledger and duplicate-cluster registry from the
   reconciled complete evidence. Exclude every
   calibration URL and cluster before rights review.
4. Validate already retained CDX-listed canonical HTML. Any additional replay
   remains a separate authorization gate. Do not access the live origin, follow
   links, retrieve attachments, or expand the URL population.
5. For each candidate, record source URL, archive timestamp, HTTP status,
   content hash, text accessibility, authority identity, rights disposition,
   exclusion reason, and provenance.
6. Run source-artifact, JSONL, duplicate, and span-accessibility validators.
7. Prepare a candidate frame and exact freeze packet containing membership,
   exclusions, clusters, seed `20260721`, PRNG, unit ordering, sample-size
   justification, and finite-population limitations.
8. Obtain separate rights/frame-freeze approval. Do not treat source-scope
   approval as freeze approval.
9. Only after freeze approval, generate blinded packets and request separate
   execution authorization.

## Contingencies

- If the complete CDX or retrieval-evidence pins cannot be reproduced, stop;
  do not fall back to the legacy 10,000-row candidates. Use Option B only with
  a new bounded frame approval, or choose Option C.
- If the nine-record ledger cannot be recovered or replaced with approved,
  provenance-complete evidence, do not freeze a fresh frame.
- If a record has inaccessible or rights-uncertain text, exclude it and retain
  the reason in the ledger; never replace it after the frame is frozen.
- If duplicate clustering removes too many units for the registered sample,
  prepare a revised sample-size packet rather than changing the seed or
  replacing units informally.
- If the remaining population cannot support an independent holdout, record
  that explicitly and keep the profile candidate; do not relax reliability
  thresholds.

## Approval decisions

No approval is needed to perform repository-local validation of the existing
candidate metadata. The CDX population is complete; no further pagination is
required or recommended. Separate decisions remain necessary for the missing
ledger disposition, fresh rights/frame freeze, and any additional archived-page
replay:

- Recommended: approve a provenance-complete nine-record ledger resolution,
  then use Option A to validate the retained CDX-listed evidence and prepare an
  exact fresh-frame packet.
- Fallback: approve Option B, restricted-local reuse of the retained 517-record
  subset, subject to a new frame packet.
- Stop: choose Option C and preserve candidate status.

None of these options authorizes annotation, maturity promotion, publication,
redistribution, training, legal certification, or release.

The CDX completion authorization has been used and the resulting metadata pins
are recorded above. A new decision is required before any additional replay of
canonical archived HTML pages; no such replay is authorized by this
reconciliation.
