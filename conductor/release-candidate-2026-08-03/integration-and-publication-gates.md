# Semantic-core integration and publication gates

## Decision and rationale

Recommended sequence:

1. integrate the isolated release branch through the repository's permitted
   squash-merge path after hosted checks pass;
2. regenerate and independently validate the candidate against the resulting
   exact `main` commit;
3. create the canonical Git tag and GitHub release;
4. create a **new** Zenodo semantic-core record from that exact archive;
5. optionally create a dedicated Hugging Face dataset repository and a separate
   OSF project/component, each from the same archive and receipt.

This sequence gives one canonical Git identity and prevents historical
destinations from being silently repurposed. The existing public Hugging Face
repository `edithatogo/fyi-archive-nz` contains source/archive records and is
not an appropriate semantic-core destination. Zenodo record `21761104` and OSF
project `5j7qa` are historical FOI-O 0.8.1 code/metadata candidates; they should
remain immutable historical context rather than being overwritten as version
0.1.0 of a narrower artifact.

## Gate A — branch integration

Gate A may authorize only:

- pushing `codex/semantic-core-release-20260804` at an exact head;
- opening a pull request against `main`;
- addressing required-check failures within the approved release scope;
- squash-merging only after required checks pass, without bypassing branch
  protections;
- read-only verification of the resulting `main` SHA; and
- repository-local regeneration and review of the manifest, archive, and
  receipt against that SHA.

It must not authorize a tag, GitHub release, upload, deposit, publication,
profile promotion, source-content redistribution, training, or legal
certification.

Recommended authorization wording (replace `[exact-head]` after the candidate
evidence commit is created):

> I authorize pushing branch `codex/semantic-core-release-20260804` at exact
> head `[exact-head]` to origin, opening a pull request against `main`, and
> squash-merging it only after required checks pass and without bypassing branch
> protections. I authorize addressing required-check failures within the exact
> release-governance scope and, after merge, read-only verification of the
> resulting `main` SHA plus repository-local regeneration and validation of the
> semantic-core manifest, archive, receipt, and review. This does not authorize
> tagging, GitHub release creation, Hugging Face repository creation or upload,
> Zenodo deposit or publication, OSF mutation, website publication, source-data
> redistribution, training, legal certification, or profile promotion.

## Gate B — canonical GitHub release

After Gate A completes, a new packet must state the actual merged `main` SHA,
canonical manifest self-pin, serialized manifest SHA-256, archive SHA-256,
receipt SHA-256, proposed tag, release title, visibility, and release notes.
GitHub tagging/release creation is then one separately authorized destination
action.

## Gate C — archival destinations

Recommended destination policy:

- Zenodo: create a new open semantic-core record only after the GitHub release;
- Hugging Face: if desired, create `edithatogo/foi-o-nz-semantic-core`, with the
  split licence represented in the dataset card and no source/archive records;
- OSF: if desired, create a separate semantic-core project/component rather
  than replacing `5j7qa`.

Each destination requires its own exact authorization naming destination
identity, visibility, uploaded archive and receipt hashes, metadata, and the
single permitted action. A successful action must produce a redacted receipt
and read-back verification before proceeding to the next destination.

## Contingencies

- Hosted-check failure: repair only in-scope defects, then regenerate all
  commit-bound candidate evidence before merge.
- Branch drift or rebase: invalidate this integration candidate and regenerate.
- Squash-merge SHA change: expected; regenerate before Gate B.
- Destination authentication or terms failure: stop that destination, preserve
  failure evidence without credentials, and keep the GitHub release independent.
- Destination metadata cannot express the split licence: attach the exact
  licence files and manifest; if the platform would misstate rights, do not
  publish there.
- Archive/read-back hash mismatch: quarantine the destination action and do not
  proceed to another destination until reconciled.
