# Bounded AU capture execution plan

Status: prepared, not executed. This plan is read-only and remains blocked
until the committed source-pack candidates, rights review, and operator packet
are attached to the run. It does not authorize publication, dataset release,
training, legal interpretation, or profile promotion.

## Pinned implementation inputs

| Input | Revision | Required check |
| --- | --- | --- |
| `fyi-cli` capture worker | `3454a24` | robots enforcement, local/shared pacing, bounded caps |
| `fyi-archive` AU rollout | `f1acf03` | explicit confirmation token, NSW-first ordering, manifest output |
| archive pilot config | `8477704` | `configs/au/jurisdiction_rollout_empirical_pilot.json`, only `NSW` and `FEDERAL` |
| archive instance | `au-rtk` | `https://www.righttoknow.org.au`, experimental only |
| jurisdictions | `NSW`, then `AU-CTH` | no other jurisdiction permitted |
| protocol | `docs/41-v2-sampling-and-annotation-protocol.md` | digest must match the approved packet or be re-approved |
| sampling candidate | `docs/42-australian-pilot-preregistration.md` | seed `20260721`, no post-freeze replacement |

## Required preflight record

Before execution, commit a run packet containing the exact legislation/source
pack candidate IDs and SHA-256 digests, the capture worker/archive revisions,
the source URL and catalog URL, retrieval timestamp, terms/robots result,
rights disposition, and the operator authorization reference. Record the
approval timestamp separately from repository recording time.

The packet must also set these fixed caps:

- maximum 50 requests per jurisdiction;
- maximum 30 minutes runtime per jurisdiction;
- maximum disk budget explicitly recorded before launch;
- two-second minimum interval, shared through one named rate-limit database;
- continue-on-error disabled unless the operator records a reason;
- no authenticated access, submissions, bypass, or unbounded discovery.

## Read-only command shape

The command is illustrative until the preflight packet is committed. It must
run in an isolated archive worktree at `f1acf03`, use the capture worker at
`3454a24`, and write only to a newly created local output directory:

```text
python scripts/run_au_live_rollout.py \
  --config configs/au/jurisdiction_rollout_empirical_pilot.json \
  --state <new-local-state.json> \
  --output-dir <new-local-output-dir> \
  --provenance <committed-provenance-record> \
  --rate-limit-db <new-local-rate-limit.db> \
  --repository edithatogo/fyi-archive \
  --capture-base-url https://www.righttoknow.org.au \
  --catalog-url https://www.righttoknow.org.au/body/all-authorities.csv \
  --delay-seconds 2 \
  --fyi-cli-version 3454a24 \
  --max-requests 50 \
  --max-runtime-minutes 30 \
  --confirm-live-capture I_CONFIRM_BOUNDED_READ_ONLY_CAPTURE
```

The confirmation token is an execution guard, not a substitute for the
operator authorization or the preflight packet. The run must stop if robots,
terms, rights, source identity, caps, or jurisdiction routing cannot be
verified. It must not create a manifest when the capture is incomplete or
when any artifact lacks a byte hash.

## Post-run immutable handoff

For each jurisdiction, retain the raw WARC/WACZ and derived record layers
separately. Verify byte count and SHA-256 locally, then verify the generated
manifest references every retained artifact and records jurisdiction, regime,
instance, coverage, rights, provenance, and capture revision. A manifest is a
candidate input to downstream NLP and process modelling only; it is not a
publication or promotion decision.
