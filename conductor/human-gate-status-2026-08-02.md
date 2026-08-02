# Human-gate status packet — 2026-08-02

Status: candidate packet for review; no release, publication, promotion, push,
tag, dispatch, or merge is authorized by this packet.

## Current repository anchor

- FOI-O branch: `codex/jurisdiction-completion-roadmap`
- Local HEAD: `1a619515041a43f0fbe2f45c68b96c0efc65e795`
- This packet is documentation-only and is not a release tag.

## Gate status

| Gate | Status | Evidence or blocker | Next action |
| --- | --- | --- | --- |
| Source/right acceptance | pending | AU source candidate evidence exists; SA HTTP 403 and QLD API registration/terms remain open | refresh rights packet and obtain bounded custodian/user decision |
| Empirical freeze | bounded approvals exist for AU-CTH/NSW pilots; remaining jurisdictions not frozen | no new population authorization | keep remaining jurisdictions candidate-only |
| Annotation execution | bounded AU-CTH/NSW approvals recorded; no new execution requested | profile-specific evidence scope | do not generalize pilot results |
| Profile promotion | AU-CTH and AU-NSW bounded maturity approvals recorded | remaining jurisdictions lack independent evidence | promote only within existing pinned scopes |
| Release | not authorized | local release checklist exists; no exact release tag or current final packet | run final checks and request exact tag/release approval |
| Publication/redistribution | not authorized | source rights differ by jurisdiction; no destination/audience approval | prepare code/metadata-only and source-text-separated packets |
| External mutation | partially completed historically; no new action authorized here | fyi-process #97, fyi-cli #286, nlp-policy-nz #235 merged; fyi-archive #327 blocked by Codecov | keep fyi-archive unmerged until 90% patch gate passes |
| Legal/accountability | pending per public claim | agents can prepare evidence but cannot certify legal outcomes | name scope and accountable approver in each packet |

## Required evidence before approval

### Promotion

Exact source-pack hashes, rights disposition, evidence-frame hash, codebook and
protocol hashes, reliability report, extractor metrics, holdout disposition,
scope limits, and candidate-to-mature decision text.

### Release

Exact commit, version registry/lock, release checklist, dependency/security
results, reproducibility command, generated-artifact inventory, rollback plan,
and unresolved external-gate list.

### Publication

Exact destination and audience, artifact inventory and hashes, licence and
attribution matrix, redaction/accessibility disposition, retention policy,
source-text exclusion list, and publication dry-run output.

### External mutation

Exact repository, branch, head, action, required checks, branch-protection
state, actor, timestamp, rollback, and explicit exclusions. A stale head
invalidates the packet.

## Recommended approval sequence

1. Close source/right packets for remaining jurisdictions, starting with the
   SA access blocker and QLD API registration.
2. Finish the fyi-archive Codecov remediation without changing its 90%
   threshold.
3. Produce one bounded promotion packet per jurisdiction; keep remaining
   profiles candidate-only until their evidence exists.
4. Produce a code-and-metadata-only release candidate; exclude source payloads
   unless their rights are separately approved.
5. Request release/tag approval separately from publication approval.
6. Request each external mutation against an exact fresh head, one action at a
   time.

## Decisions for the user when the next packet is ready

### Option A — staged approvals (recommended)

Approve each packet only after its exact hashes and destination are presented.
This minimizes stale approvals and keeps release, publication, and mutation
independent.

### Option B — omnibus approval

Approve a group of actions in one statement. Faster, but unsafe when source
rights, destination, head, or release contents may change.

### Option C — local-only closeout

Complete and archive all candidate packets without external action. Safest when
rights, credentials, or custodians are unavailable, but it leaves release and
publication incomplete.

Recommendation: Option A, with Option C as the automatic fallback for any
stale, blocked, or rights-uncertain packet.
