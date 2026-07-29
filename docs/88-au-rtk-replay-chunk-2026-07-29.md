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
