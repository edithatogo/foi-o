# AU RightToKnow bounded replay chunk

Recorded: 2026-07-29. This is operational evidence only. It is not an
empirical source population, immutable manifest, release artifact, or legal
certification.

## Pinned inputs and boundary

- CDX SHA-256: `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`
- Selection SHA-256: `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`
- Selection population: the approved 2,082 canonical request slugs
- Chunk offset: `0`
- Chunk limit: `50`
- Workers: `2`
- Launch delay: `0.75` seconds
- Request timeout: `20` seconds
- Retries: `1`
- Circuit-breaker bound: `1000` failures

Replay used only CDX-listed Internet Archive URLs. It did not access the live
RightToKnow origin, follow links, retrieve attachments, or expand the URL
population.

## Result

The chunk resolved all 50 selected records:

- successful captures: `6`
- failed captures: `44`
- pending records: `0`
- circuit opened: `false`
- normalized candidate SHA-256:
  `8c7843a6755c372eec7536d2c483d7bb12160c54f9c77e6680647a9409a5f397`
- result status: `candidate_non_final`
- manifest finalization authorized: `false`

The 44 failed records are failure evidence, not source records. The six
successful captures remain bounded candidate material and are not admitted to
an empirical frame by this record. No source bytes were published,
redistributed, or used to finalize a manifest.

## Follow-up chunk

A second exact chunk was run with the same replay controls, offset `50` and
limit `50`. It resolved all 50 records with `0` successful captures and `50`
failures. Its normalized candidate SHA-256 is
`f706dbcb4047b8e870ad1b2005d8f4985b679c8b53df34d9f4e6bf64118a2180`.
The result was again `candidate_non_final`, with no pending records and
`manifest_finalization_authorized: false`. The second chunk is likewise
failure evidence only.

## Failure classification

The failed record checkpoints were inspected locally. The first chunk had 44
failures with diagnostic `[Errno 61] Connection refused`; the second had 50
failures with the same diagnostic. This identifies an Internet Archive
endpoint availability/refusal condition rather than a selection, URL-boundary,
parser, or validator error. No retry was expanded beyond the authorized
canonical URLs.

## Fresh retry

A fresh 10-record retry at offset `100` and limit `10`, using the same
archive-only controls, produced `0` successful captures and `10` failures.
The normalized candidate SHA-256 is
`c4e8ebf28330192ffc0d67058d35249ef3134cacd4d47a624b75a43b57707a4d`.
The result remained `candidate_non_final`, with no pending records and
`manifest_finalization_authorized: false`. This confirms that the connection
refusal persisted during a later bounded retry.

## Remediation retry

A direct bounded HEAD request to the first CDX-listed snapshot was reachable.
The replay was then retried at offset `100`, limit `10`, with one worker,
1-second launch delay, 30-second timeout, and two retries. All 10 captures
succeeded; there were no failures or pending records. The normalized candidate
SHA-256 was
`83a57f6fdf49dd4b45ca757ac5d6d416cbdecefa2f787498b6858ac54c3f44f1`.

The replay CLI defaults were hardened in fyi-archive commit `814a2f5` to the
proven serial settings (one worker and 1-second pacing); callers may still
override them explicitly. This addresses the repository-side concurrency
contributor but does not by itself complete the 2,082-record replay or permit
manifest finalization.

The same remediation was then resumed over offset `100`, limit `100`, using
one worker, 0.5-second pacing, a 20-second timeout, and one retry. Checkpoint
resumption completed all 100 records with `100` successful captures, `0`
failures, and `0` pending records. The normalized candidate SHA-256 was
`640870c9a7bbc5cc2029e50fed584de6184f812d6ddf501db0203975eb1aa091`.
This remains candidate-only and does not authorize manifest finalization.

## Serial replay milestone

Using explicit 20-record chunks with one worker, bounded pacing, checkpoint
resumption, and the pinned selection, offsets `0` through `999` are covered.
The current aggregate is `999` successful captures, `1` failed capture, and
`0` pending records. The sole failed record is the selected JSON URL for
`acting_treasurer_scott_morrisons`; both the replay and a direct bounded HTTP
check returned `404 Not Found` for its CDX-listed timestamp. It remains a
failure-evidence exception and is not silently replaced by another capture.

All successful outputs remain candidate-only. The remaining approved offsets
`1000` through `2081` still require replay and validation.

## Partial consolidation and classification

The successful checkpoint records currently available were consolidated into a
restricted-local, non-final candidate and classified using the existing
explicit-authority classifier. The candidate is bound to selection SHA-256
`a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51` and is
not a complete replay or manifest input.

| Output | Records | SHA-256 |
| --- | ---: | --- |
| AU-CTH | 877 | `d939080ec655236a66d83c02f0a67603647592c2bbb8bab9b96dbcc21ffe13ac` |
| AU-NSW | 77 | `b51bd0f0aac1b12b6047c05e65ed8f71aa2513043431922f1ee9c5acf1c8cbdb` |
| Out of scope | 69 | `6e5f46a36fc5941b91a188d69c637af7c8eb5fdf957be1cb0bf0dfb935e61aeb` |
| Unresolved | 147 | `6efdc2d409569a53dffd17c0afcf3b4daba37a837e089fddc1b9dd297121a478` |

The partial classification summary SHA-256 is
`5247ad342bbcb73429d041d2c2371a1728489264451e3f34c2475858fe5c6be1`.
Ten selected slugs remain failed or uncaptured, including one persistent
404-selected JSON snapshot and nine transient/replay failures. The partial
outputs remain candidate-only and are not eligible for empirical freezing or
manifest finalization.

## Validator outcome and corrected JSONL hashes

The source-artifact validator was run against the existing CTH and NSW
source-pack candidate envelopes. It failed closed for both because they are
source-pack metadata envelopes, not `foi-o.australian-source-artifact.v0.1.0`
records artifacts with an approved frozen-candidate status and `records_path`.
They were not promoted or rewritten to evade that boundary.

The first partial JSONL emission was also rejected by the exact-membership
validator because it omitted `canonical_slug`. That defect was corrected by
retaining the slug in every classified record. The corrected JSONL validator
run passed for all 1,170 consolidated records. Corrected hashes are:

| Output | Records | SHA-256 |
| --- | ---: | --- |
| AU-CTH | 877 | `1747f18cf98de07fa61670e595da941b185ec364d122dfb3abc227dd18050334` |
| AU-NSW | 77 | `b77ba1f10f9ca0d555d2c517c5eb4383b65cdbcb68eed44cffee93ef66a25aea` |
| Out of scope | 69 | `652f0f98bd44b8b3244a5a7083e2bbf5e4fc43fcfd568a3e378aa10aebfc2a05` |
| Unresolved | 147 | `39c924017be366d2865b4af3d9905f84bb864fab32656b721a31a5c1f1f4803f` |
| Replay index | 1,170 | `d82ae6e51ebd905bf0283746491e587a1e72d35d0f74bcfaf299048f18feb2bd` |

These remain partial, restricted-local, non-final candidates.

## Replay continuation state

Subsequent serial checkpointing extended coverage to offsets `0` through
`1279`: `1,234` successful captures, `46` failures, and `0` pending records.
The current failure ranges are `0–19` (1), `1040–1059` (4), `1180–1199` (1),
`1240–1259` (20), and `1260–1279` (20). The latter two ranges returned
`[Errno 61] Connection refused` for every request and remain retryable failure
evidence. No records were reclassified as successful without a captured and
hash-verified response.

## Candidate immutable-manifest input packet

A restricted-local manifest-input packet was assembled at the current
milestone. It contains the approved CDX and selection metadata, retrieval
evidence, replay index, corrected classified JSONL outputs, partial summary,
and explicit failure ledger. The packet declares 10 hashed input artifacts,
covers 1,170 captured records, and records 10 failed records. Its status
artifact SHA-256 is
`dcbdd6615630e01d8e8e473f03619c8b3bd9845d1916e267507438c52e1661f2`.

The generated historical-manifest candidate has SHA-256
`137bdd0fe7c7fe783b5d0b28313c72f013d471bab0cc20dda2f6603630af3331`.
The build validator confirmed every declared artifact hash and byte count.
This is a preparation packet only: `status: candidate_non_final`,
`manifest_finalization_authorized: false`, and no publication or redistribution.
It cannot become an immutable final manifest until all 2,082 approved records
are successfully replayed or explicitly dispositioned under the approved
boundary.
