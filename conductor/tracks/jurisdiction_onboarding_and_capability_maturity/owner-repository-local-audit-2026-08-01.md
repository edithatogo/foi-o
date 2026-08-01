# Owner-repository local audit — 2026-08-01

This is a read-only local checkout audit. It is not hosted-branch evidence and
does not authorize push, pull request, merge, release, runtime activation, or
source capture.

| Repository | Local branch | HEAD | Local state | Readiness |
| --- | --- | --- | --- | --- |
| legislation | codex/australian-source-pack-readiness | 636c79b | dirty; ahead 42 | candidate only |
| fyi-cli | master | 0b6c36b | dirty; ahead 2, behind 82 | not reconciled |
| fyi-archive | codex/fyi-archive-type-repair | 8374879 | dirty; upstream gone | not reconciled |
| nlp-policy-nz | codex/archive-track92-actions-20260716 | 5a65be9 | dirty; upstream gone | not reconciled |
| foi-process | codex/citation-metadata-20260714 | dc2880f | clean; upstream gone | not reconciled |

## Disposition

The checkouts are preserved exactly. Their dirty files and branch histories
must not be reset or inferred to represent hosted integration. The recommended
next step is to reconcile each repository independently against its exact
target default branch, then present hash-bound push/PR options. Until that
occurs, the six owner-repository phase contracts and all jurisdiction tranches
remain blocked.

## Safe contingency

If a repository cannot be reconciled without discarding local work, create a
separate clean checkout or bundle for review; do not reset, force-push, or
overwrite the existing checkout.
