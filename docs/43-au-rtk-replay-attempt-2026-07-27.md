# AU RightToKnow bounded replay attempt

## Status

The authorized replay is complete and independently validated. No immutable
manifest has been finalized. The replay completed with one persistent Internet
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
The Internet Archive edge later recovered. At `2026-07-27T08:05:20Z`, all
2,082 selected captures were present as matched restricted-local raw and parsed
checkpoints, with zero failures and no open circuit. Parser-v3 local
reprocessing completed at `2026-07-27T08:05:58Z`.

The normalized candidate JSONL has SHA-256
`3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807`.
The schema-validated jurisdiction candidate has SHA-256
`98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab`
and exactly partitions the 2,082 records:

- AU-CTH: 1,578
- AU-NSW: 179
- out of scope: 115
- unresolved: 210

The independent FOI-O oracle returned `ok: true` for the exact partition,
source provenance, retained raw hashes, record hashes, path containment, and
non-finalization boundaries.

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

The separately authorized 1,716-query metadata-only completion lookup for the
858 excluded slugs is in progress. Any newly discovered canonical captures
must be presented as a hash-pinned candidate for separate replay approval.

Immutable-manifest finalization, empirical freezing, annotation, publication,
redistribution, training, legal certification, profile promotion, push, pull
request, and merge remain prohibited.
