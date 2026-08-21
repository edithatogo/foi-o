# AU-RTK ledger replacement verification approval packet

Status: awaiting corrected exact-hash approval.

## Candidate

- Path: `examples/v2/au-rtk-nine-failure-ledger-replacement.pending.json`
- SHA-256: `8da8534a2f663bab7b6ed263797baf16aeb9ae00665e1e35e3ba359228180b42`
- Selection SHA-256: `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`
- CDX SHA-256: `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`
- Parent manifest SHA-256: `246cd65c3c60733fb31478b07f12bd251877b1efe9559643d5c566bc337d0ff8`
- Recorded approved ledger SHA-256: `0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`

## Boundary correction

The previously supplied authorization omitted part of the candidate hash and
therefore does not bind to this artifact. It is not applied. The candidate
remains unverified and unchanged.

## Correct authorization wording

> I authorize independent restricted-local verification of pending candidate
> SHA-256 `8da8534a2f663bab7b6ed263797baf16aeb9ae00665e1e35e3ba359228180b42`
> against its pinned selection, CDX, and parent-manifest inputs. This
> authorizes verification and preparation of a replacement-ledger decision
> packet only. It does not authorize treating the records as HTTP 404,
> manifest finalization, frame freezing, annotation, evaluation, publication,
> or release.

Verification must remain blocked until that exact statement is approved.
