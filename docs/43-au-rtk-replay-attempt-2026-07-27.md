# AU RightToKnow bounded replay attempt

## Status

Recovery remains incomplete and no candidate manifest can be finalized. The
checkpointed replay has resumed successfully with one persistent Internet
Archive connection and two-second launch pacing.

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
The Internet Archive edge later recovered. At `2026-07-27T06:05:54Z`, at least
1,200 of 2,082 selected captures were present as matched restricted-local raw
and parsed checkpoints, with no failure record in the resumed run.

The local replay implementation now:

- reuses one paced connection and stops after a bounded consecutive-failure
  circuit;
- reparses all retained raw captures locally with parser v3 before
  classification;
- extracts authority identity from the actual `/body/<slug>` anchor while
  excluding `/body/list` navigation;
- reads GIPA/FOI/RTI only from the structured request-header label;
- separates AU-CTH, AU-NSW, explicit out-of-scope, and unresolved records;
- creates a deterministic raw/parsed replay index and non-final, hash-pinned
  jurisdiction outputs;
- validates exact partition membership, source provenance, path containment,
  and publication/finalization prohibitions both in `fyi-archive` and through
  an independent FOI-O oracle.

No live RightToKnow origin was contacted. No links or attachments were fetched.
Successful raw captures and current parsed checkpoints remain restricted-local;
the earlier attempt's aggregate failure counts are retained above.

## Remaining boundary

The authorization remains usable for the active checkpointed continuation, but
the Conductor bounded-retry rule prevents an unbounded retry loop. Final
parser-v3 reprocessing, AU-CTH/AU-NSW classification, normalized candidate
JSONL validation, and non-final manifest preparation must wait for all 2,082
authorized selections to be accounted for.

Immutable-manifest finalization, empirical freezing, annotation, publication,
redistribution, training, legal certification, profile promotion, push, pull
request, and merge remain prohibited.
