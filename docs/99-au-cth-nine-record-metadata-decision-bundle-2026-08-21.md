# AU-CTH nine-record metadata decision bundle

Status: prepared locally; awaiting one sole-maintainer decision. This bundle
does not create an exclusion candidate or alter a manifest.

## Verified metadata-only inputs

- Repository revision: `b64f22a6981a4e3c84555708a953efb8359b8faa`.
- Pending candidate: `8da8534a2f663bab7b6ed263797baf16aeb9ae00665e1e35e3ba359228180b42`.
- Selection: `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`.
- CDX: `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`.
- Parent manifest: `246cd65c3c60733fb31478b07f12bd251877b1efe9559643d5c566bc337d0ff8`.
- Legacy ledger remains absent: `0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`.

The owner-only v2 receipt is valid JSON. Its serialized file SHA-256 is
`b7c3cfe86b2fcbd4405159892c7cd5bebdaa95b5f1c33ab4dda9aeeb62cc53b1`; its
canonical hash, excluding its declared receipt hash, is
`12c4a63d72c9dd7a942fe523178b95abb7361e73b349f9728c13c2a4f7a87388`.
It verifies nine unique candidate positions against the selection, CDX, and
parent-manifest exclusion set, without replay or source-content inspection.

## Agent advisory panel synthesis

The provenance-and-rights, technical-reproducibility, and operational-risk
roles agree that the metadata result cannot establish HTTP 404. The legacy
failure-ledger validators must remain blocked because they require the missing
ledger bytes and explicit 404 diagnostics. The malformed v1 receipt is retained
as invalidated; the v2 receipt supersedes it only as a metadata verification.

## Options

### A. Prepare a non-final unavailable/unverified exclusion candidate (recommended)

Authorize preparation and validation only of a new candidate that marks exactly
the nine records as `unavailable/unverified full-text` exclusions. It must retain
all pins, preserve the historical manifest, and state that the candidate is not
a replacement HTTP-404 ledger.

### B. Keep the evidence blocker open

Preserve the current candidate and pursue only a future byte-identical recovery
of the legacy ledger. This makes no new evidence object but leaves all fresh
AU-CTH work blocked indefinitely unless recovery succeeds.

### C. Defer

Record no additional candidate and retain the existing fail-closed block.

## Recommendation and stop conditions

Recommend A because it preserves the evidence boundary while allowing a
reviewable, non-final disposition. Stop if any pin, membership, count, JSON
integrity check, or boundary flag drifts; if source-content access, replay,
origin access, ledger reconstruction, or HTTP-404 inference becomes necessary;
or if any downstream empirical operation is proposed.

## Exact approval wording for Option A

> I authorize preparation and local validation only of one non-final AU-CTH
> candidate that records the exact nine positions verified in receipt v2 as
> `unavailable/unverified full-text` exclusions, pinned to candidate
> `8da8534a2f663bab7b6ed263797baf16aeb9ae00665e1e35e3ba359228180b42`,
> selection `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`,
> CDX `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`,
> and parent manifest `246cd65c3c60733fb31478b07f12bd251877b1efe9559643d5c566bc337d0ff8`.
> This does not authorize an HTTP-404 finding, ledger recovery, manifest
> modification or finalization, frame freezing, sampling, annotation,
> evaluation, publication, release, push, pull request, or merge.
