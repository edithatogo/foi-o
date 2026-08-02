# AU-CTH fresh-holdout rights and freeze plan

## Current evidence

The current AU-CTH candidate inventory is not freezeable:

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

The authoritative candidate records are
`examples/v2/au-cth-fresh-holdout-coverage.pending.json` and
`examples/v2/au-cth-fresh-holdout-source-approval.pending.json`.

The exact-scope completion attempt on 2026-08-02 reproduced the complete
Internet Archive CDX artifact: 26 pages, 26,000 records, CDX SHA-256
`954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`, and
retrieval-evidence SHA-256
`b6dc23e32048b1ef252b2157080280d7e411870d0fe0f4ca181ca8a4e8160d64`. This
resolves pagination completeness for the metadata artifact only. It does not
resolve authority identity, rights, accessible text, duplicate-cluster
exclusions, or empirical-frame eligibility.

## Options

### Option A — complete the CDX population and validate records (recommended)

Retrieve only the remaining exact CDX pages for the approved URL scope, verify
the page chain and raw export hash, select canonical request URLs, exclude the
four calibration URLs and every duplicate cluster containing one, then validate
the selected archived HTML artifacts. Record rights/accessibility disposition
per candidate before preparing a freeze packet.

Rationale: this provides the strongest evidence that the holdout frame is
complete within its declared scope and avoids treating a bounded truncation as a
population frame.

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

1. Authorize one bounded completion of the exact 27-page CDX scope, or confirm
   that the existing candidate is the intended limited scope.
2. Verify raw CDX bytes, page continuity, query parameters, retrieval time,
   export hash, and coverage counts.
3. Build a canonical URL ledger and duplicate-cluster registry. Exclude every
   calibration URL and cluster before rights review.
4. After separate bounded replay authorization, replay only CDX-listed
   canonical HTML captures, or validate already retained
   HTML. Do not access the live origin, follow links, retrieve attachments, or
   expand the URL population.
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

- If pagination cannot be completed, do not claim complete-population coverage;
  use Option B only with a new bounded frame approval, or choose Option C.
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
candidate metadata. A decision is needed before any network CDX completion or
archived-page replay:

- Recommended: approve Option A, exact-scope CDX completion and bounded
  CDX-listed HTML validation only.
- Fallback: approve Option B, restricted-local reuse of the retained 517-record
  subset, subject to a new frame packet.
- Stop: choose Option C and preserve candidate status.

None of these options authorizes annotation, maturity promotion, publication,
redistribution, training, legal certification, or release.

The CDX completion authorization has now been used for metadata retrieval. A
new decision is required before replaying canonical archived HTML pages.
