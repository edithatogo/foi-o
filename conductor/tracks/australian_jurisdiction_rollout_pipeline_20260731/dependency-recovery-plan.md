# Australian rollout dependency recovery plan

## Scope

This plan covers the four owner repositories required by the Australian
rollout: `fyi-cli`, `fyi-archive`, `legislation`, and `nlp-policy-nz`. It also
tracks the already-identified `foi-process` process-template dependency. It is
repository and provenance planning only; it does not activate providers,
retrieve governed sources, or authorize profile promotion.

## Current dependency state

| Repository | Local candidate | Required role | Current gate |
| --- | --- | --- | --- |
| `fyi-cli` | `3f3befa8acb07dce492ce41e99457d6da5acfa88` | Australian capability audit and capture contracts | verify candidate, then push/hosted review |
| `fyi-archive` | `af4c0a47e2d589f295ba2dfebee0f3f7681690f7` | checkpointed content-addressed Wayback replay | verify candidate, then push/hosted review |
| `legislation` | PR #106 head `0c0efe877f0b8eb7e5f05a2d89aeec82a09dbf5c` | legislation/Gazette source-pack control | protected merge gate |
| `nlp-policy-nz` | `2a49a516252d6e2c765c4d8a6e53336226e273bf` | config-driven profile foundation | verify candidate, then push/hosted review |
| `foi-process` | `8bc0c2c6022a4de08d2e52515af4885ee598a094` | paired Mermaid/BPMN process template | verify candidate, then push/hosted review |

The owner checkouts must be treated as dirty and unrelated work preserved. No
candidate is assumed to be present in the active branch merely because its
commit exists in a temporary workspace.

## Dependency-ordered recovery

1. Locate each candidate in its producing temporary workspace or owner backup.
2. Verify commit existence, ancestry, Git note, worktree cleanliness of the
   candidate workspace, and candidate-specific test evidence. Do not overwrite
   the active owner checkout.
3. Compare candidate content and Git notes with the dependency register and
   record a candidate receipt in FOI-O.
4. Run local contract checks in each candidate workspace, preserving skipped
   network tests as external gates.
5. Push only the exact verified candidate branches to their owner remotes after
   explicit authorization.
6. Open draft PRs referencing the originating issue, candidate SHA, scope, and
   Conductor track. Monitor required checks and address only in-scope failures.
7. Merge only after exact-head protected checks pass and a separate merge gate
   is authorized.
8. After the shared dependencies are hosted and merged, execute the readiness
   sequence: SA/WA/NT, then VIC/TAS, then ACT/QLD when their source blockers
   clear.

## Source and provider dependencies

- Legislation adapters require official source identity, format, effective-date
  handling, provenance, terms, and parser fixtures before runtime activation.
- `fyi-cli` and `fyi-archive` support capture/replay mechanics only; they do
  not establish jurisdiction, rights, or empirical eligibility.
- `nlp-policy-nz` supplies ontology/profile configuration and extraction
  contracts; it does not promote a profile or certify legal outcomes.
- `foi-process` supplies process-model parity and cannot authorize source use.
- Queensland additionally requires maintainer registration, credential
  custody, terms/rates, and authentic fixtures.
- ACT additionally requires source-track restoration, authority identity
  resolution, and authoritative-PDF policy.

## Options

### Option A — verify and promote the existing exact candidates through hosted review (recommended)

Recover the exact local candidate commits, verify them, then push/open draft
PRs in dependency order and merge only after protected checks and explicit
merge approvals.

Rationale: preserves reviewed work, avoids duplicate implementation, and gives
each owner repository its own CI and review evidence.

### Option B — rebuild candidates in the active owner checkouts

Reimplement or cherry-pick equivalent changes into the current branches,
preserving dirty work and creating new candidate SHAs.

Rationale: useful only if a candidate workspace is corrupted or stale; it
creates new hashes and therefore requires fresh review and approval.

### Option C — retain local-only candidates and continue FOI-O contract work

Do not push or open PRs; continue local validators, source-shape manifests,
approval packets, and jurisdiction-neutral fixtures.

Rationale: safest when external mutation is not authorized, but it leaves the
shared dependency critical path unresolved.

Recommendation: Option A, with Option C running in parallel. Use Option B only
when exact candidate recovery fails.

## Contingencies

- Candidate missing or hash mismatch: stop that repository lane, preserve the
  receipt, and prepare a new candidate; do not force-push or rewrite history.
- Dirty owner checkout: use the producing workspace or a new isolated worktree;
  never reset, stash destructively, or overwrite unrelated changes.
- Hosted check failure: run one bounded repair loop against the exact failure;
  if it persists, record the failure and present it for decision.
- Legislation PR #106 changes head: revalidate the new exact head before merge.
- QLD registration unavailable: continue SA/WA/NT/VIC/TAS preparation and keep
  QLD runtime activation disabled.
- Authority or rights ambiguity: retain unresolved classification and do not
  create an empirical frame.

## Decisions and approvals

No decision is needed for local candidate verification or preparation of draft
packets. A decision is required before hosted mutation:

- Recommended: authorize verification, push of the five exact candidates, draft
  PR creation, and hosted-check remediation, with merge separately gated.
- Conservative: authorize only local verification and draft packet preparation.
- Rebuild: authorize new candidate creation if exact recovery fails.

None of these options authorizes source capture/replay, rights approval,
empirical freezing, annotation, publication, redistribution, training, legal
certification, or profile promotion.
