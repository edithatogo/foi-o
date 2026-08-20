# AU-CTH replay compatibility and failure-ledger recovery outcome

Status: fail-closed; fresh evaluation remains blocked.

## Compatibility result

The retained replay summary at
`/Volumes/PortableSSD/foio-restricted/au-rtk-30236042144/replay/summary.json`
uses `fyi-archive.au-rtk-replay-result.v1`. It is an aggregate replay
envelope, not a jurisdiction-classification candidate. A versioned FOI-O
compatibility validator now checks its approved selection, 2,082-record
coverage, zero failed/pending state, closed circuit, non-final status, and
normalized-candidate pin
`3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807`.
Classification and source validators still run separately.

## Ledger recovery result

The restricted immutable manifest records the approved failure-ledger hash
`0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`, but a
byte-identical ledger file was not found in the restricted evidence store,
repository history, Git notes, or temporary recovery locations. The manifest
is not treated as a substitute because it contains only the ledger hash and
disposition summary.

The nine-record ledger therefore remains **unrecovered and unverified**. No
reconstructed ledger has been created, and no new replay or origin access was
performed.

A non-final metadata-only replacement candidate has now been prepared at
`examples/v2/au-rtk-nine-failure-ledger-replacement.pending.json`.
Its SHA-256 is
`8da8534a2f663bab7b6ed263797baf16aeb9ae00665e1e35e3ba359228180b42`.
It contains the nine approved selection members and their selection metadata,
but every disposition is explicitly `unverified`; it does not assert that any
record returned HTTP 404 and cannot be passed to the existing immutable-manifest
validator.

## Recovery receipts

The read-only recovery checked:

- fyi-archive Actions run `30236042144`, artifact
  `alaveteli-all-captures-au-rtk-30236042144`, artifact ID `8641731722`, which
  contains the CDX export, paginated CDX pages, checkpoint, and retrieval
  evidence only;
- the retained restricted evidence store;
- the retained fyi-archive replay checkout and its Git history;
- FOI-O repository history and Git notes.

The downloaded CDX artifact rehashed to
`954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`; the
retrieval evidence rehashed to
`0795be14775616416f61fb4131c397e7f2496f72c9fc534a357a98ec6e827331`. Neither
contains the nine-record ledger, and neither is being treated as a ledger
replacement.

## Consequence

The compatibility blocker is addressed in code and covered by focused tests.
The evidence blocker remains: recover the exact ledger bytes or approve a
provenance-complete replacement after independent verification. The pending
candidate is not yet such an approved replacement and cannot authorize fresh
frame validation, execution, annotation, or maturity evaluation.
