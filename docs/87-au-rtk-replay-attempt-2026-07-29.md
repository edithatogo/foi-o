# AU RightToKnow bounded replay attempt

Recorded: 2026-07-29. This is negative/operational evidence only and is not a
source population, empirical frame, immutable manifest, or release artifact.

## Inputs

- CDX artifact: `alaveteli-all-captures-au-rtk-30236042144`
- CDX SHA-256: `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`
- Selection SHA-256: `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`
- Authorized population: 2,082 canonical request slugs

## Attempt

The replay used the committed archive-only replay implementation with two
workers, a 0.75-second launch delay, 45-second request timeout, four retries,
and a 1,000-failure circuit-breaker bound. It was stopped after slow progress
produced only 25 partial record files and 3 raw files. No complete summary or
normalized candidate was produced.

The partial files are discarded from consideration. They must not be merged,
imported, classified as a population, used for an empirical frame, or used to
finalize a manifest. The approved CDX and selection inputs remain valid and
available for a future bounded retry.

## Disposition

`status: failed_incomplete_replay`

No source bytes were published, uploaded, redistributed, or used for empirical
analysis. A complete replay remains an operational Internet Archive
availability/performance gate, not an authorization gap.
