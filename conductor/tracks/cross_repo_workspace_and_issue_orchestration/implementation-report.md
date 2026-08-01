# Implementation report

Date: 2026-08-01

## Recommended dependency sequence

1. Keep the authoritative FOI-O checkout and all sibling checkouts read-only
   during audit. Record exact paths, branches, SHAs, dirty state and remotes.
2. Run the workspace doctor and duplicate-remote audit. Preserve duplicate
   identities until a human explicitly chooses a canonical checkout and a
   recoverable disposition for each duplicate.
3. Validate the local contract and reconcile the versioned issue map and
   project references. Treat hosted issue/project state as evidence, not as
   permission to mutate it.
4. Run repository-native tests, schema/workflow validators, lint, formatting
   and diff checks; record the results in the track review and evidence ledger.
5. Only after the above are green may a separately authorized operator perform
   external issue/project updates, publication, submission, or other mutation.

## Blockers and contingencies

| Blocker | Recommended handling | Fallback |
| --- | --- | --- |
| Duplicate FOI-O or fyi-archive remote identities | Preserve both and request a human-selected canonical path plus a recovery plan | Continue local validation with both identities explicitly listed |
| Hosted issue/project state is stale or unavailable | Use the versioned issue map and `issue-export.json` as a dry-run snapshot | Record an external-evidence gap and do not infer synchronization |
| GitHub mutation is not authorized or checks are pending | Keep changes local and leave the human gate pending | Prepare an exact, hash-bound action packet without executing it |
| Optional external tooling is unavailable | Run the repository-native Python validators and record the missing gate separately | Defer only the affected external check; do not weaken local contracts |

## Current disposition

Local implementation and review evidence are complete for the read-only slice.
The track remains in progress because duplicate workspace disposition and all
external mutation, publication, submission, and profile/legal gates are still
open. No external action is implied by this report.

The exact choices and paths are recorded in `closeout-decision-packet.md`.
The recommended preservation disposition has been accepted; no checkout
cleanup, relocation or deletion is authorized by that decision.

The remaining external-gate choices are recorded in
`external-gate-approval-packet.md`. The local issue/project references contain
an identified project-number discrepancy (cross-repository export project 29
versus the FOI-O integration contract's project 10), so no synchronization is
inferred or performed.
