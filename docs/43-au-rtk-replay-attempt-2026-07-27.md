# AU RightToKnow bounded replay attempt

## Status

Recovery remains incomplete and no candidate manifest can be finalized.

The amended authorization selected 2,082 canonical request pages:

- 1,225 latest successful canonical JSON captures
- 857 latest successful canonical primary HTML captures
- 858 attachment-only slugs excluded from replay

The exact restricted-local replay selection has SHA-256
`a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`.

The exact targeted CDX metadata plan for the two canonical URL forms of each
excluded slug has 1,716 queries and SHA-256
`ac402c3d69e6140772629e5ecb55f0138c891121a42c2fa7a180850260742d3b`.

## Attempt evidence

The first bounded run used four workers and was stopped when Internet Archive
began refusing most TCP connections:

- replay captures completed: 20
- replay checkpoints failed with `[Errno 61] Connection refused`: 116
- targeted CDX checkpoints failed with `[Errno 61] Connection refused`: 46

A subsequent single exact CDX request also failed at connection establishment.
No live RightToKnow origin was contacted. No links or attachments were fetched.
Every completed or failed unit is preserved as a restricted-local checkpoint.

## Remaining boundary

The authorization remains usable for checkpointed continuation when Internet
Archive is available, but the Conductor bounded-retry rule prevents an
unbounded retry loop. AU-CTH/AU-NSW classification, normalized candidate JSONL
validation, and non-final manifest preparation must wait for replay completion.

Immutable-manifest finalization, empirical freezing, annotation, publication,
redistribution, training, legal certification, profile promotion, push, pull
request, and merge remain prohibited.
