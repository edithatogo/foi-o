# Jurisdiction onboarding dependency-gate plan

## Current state

The FOI-O programme contracts, six-phase completion rule, issue hierarchy, and
coverage map are repository-complete. The remaining plan items depend on six
owner repositories and on jurisdiction-specific evidence. A linked issue is
not evidence that an owner-repository track has landed or that a jurisdiction
has passed its source, rights, empirical, or maturity phases.

## Recommended sequence

1. Reconcile exact owner-repository track heads and hosted-check status for
   legislation, fyi-cli, fyi-archive, nlp-policy-nz, and foi-process.
2. Complete the shared archive/capture/provenance prerequisite before starting
   a new jurisdiction tranche.
3. Execute one dependency-first tranche at a time: SA/WA/NT, then VIC/TAS,
   then ACT/QLD, with separate evidence packets for each jurisdiction.
4. Obtain operator and rights authorization before live capture or replay.
5. Freeze source frames, run annotation/adjudication, and review maturity
   independently for each profile.
6. Keep publication, redistribution, profile promotion, and external mutation
   as separate final gates.

## Options

### Option A — local dependency handoff (recommended)

Maintain the map, issue links, and bounded readiness packets locally while
waiting for exact owner-repository SHAs and approvals. This is reversible and
has no external side effects.

### Option B — authorize owner-repository integration

Provide exact repository, branch/PR, commit SHA, operation, and required-check
conditions for each owner repository. A passing local check does not authorize
push, merge, or runtime activation.

### Option C — authorize one jurisdiction tranche

Provide the jurisdiction, official source scope, capture/replay limits, rights
terms, and hash-bound authorization. This should be done one tranche at a time
and does not authorize profile promotion or publication.

## Contingencies

- Missing or stale owner-repository evidence blocks the dependent phase; retain
  the last known hash and record a negative receipt.
- A source or rights failure produces an exclusion/failure packet rather than
  population expansion or an inferred legal conclusion.
- A changed input invalidates downstream frames, annotations, and maturity
  packets; regenerate only from the new pinned inputs.
- If no exact authorization is supplied, preserve local readiness and do not
  capture, push, merge, publish, or promote.
