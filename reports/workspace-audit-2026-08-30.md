# FOI-O live workspace audit — 2026-07-21

This audit supersedes the bundled 2026-07-20 snapshot. Exact local state is
locked in `workspace.lock.yaml`; the source ZIP is identified by SHA-256
`4877122cf59b879d6121cd27054f99a3c9e1efee64771c22160fb487badfb528` and its
bundle validator passed before this audit.

## Current state

The active checkout is `https://github.com/edithatogo/foi-o.git` at commit
`c4702380dfb50b0b856bbb1fc20953822dfaeee5`, branch
`codex/australia-profile-quality`, whose remote branch is gone. It contains
four modified tracked files and seven categories of uncommitted/untracked work,
including the capability-contract implementation. Those files are preserved.
No destructive Git operation was used.

Required sibling identities were resolved by remote URL. `rac-conformance` is
the dirty local clone at `rulesandprocesses`; `foi-process` and `rulespec-nz`
were the only clean required clones and were fetched with tags/prune. Dirty
clones were not fetched or pulled. `sourceright` and `authentext` are available
on GitHub but not locally cloned.

## GitHub re-audit

On 2026-07-21, authenticated `gh` read the repository metadata, default
branches, releases, open PRs and issue searches for all required repositories,
plus `gemini-cli-extensions/conductor`. No exact duplicate was found for the
four proposed work packages in `issue-dry-run.json`. Current relevant public
surfaces include FOI-O issues #24/#29–#33, rac-conformance #30/#38/#45/#50,
fyi-cli #140/#196/#228/#231, fyi-archive #187/#188/#196, legislation #49–#64,
and the current Conductor release `v0.4.1` with open upstream work on
worktree isolation (#161), track modification (#149), deterministic planning
(#155), long inputs (#154), and behavioural evals (#116).

The live repositories have moved since the bundled audit: fyi-cli and
fyi-archive have newer public pushes/releases, foi-process has a newer `main`
and its local feature branch was deleted upstream, and the Conductor project
has current maintenance fixes (#174/#175). These changes are recorded as audit
inputs, not silently imported into this dirty checkout.

## GitHub programme wiring

GitHub Project #29, `FOI-O Global Next-Generation Programme`, was created on
2026-07-21. It contains 24 items: the 14 primary ZIP workstream mappings plus
existing child issues from the Australian and fyi-cli issue hierarchies. The
primary workstream item IDs and status are recorded in
`conductor/cross-repo-issue-map.yaml`; all primary items are `In Progress`.

## Boundaries

Live capture, human annotation/adjudication, legal/profile promotion, ontology
registry submission, manuscript submission, release/push/merge, and dataset or
paper publication remain blocked by explicit human gates. Platform compatibility
is not treated as legal comparability or permission to crawl.

## Duplicate clone re-audit

The bounded workspace doctor found a second local clone with the `foi-o` remote
identity at `/Volumes/PortableSSD/GitHub/foi-o-wiring`, commit
`a94d22fea5e0fdbfa6cd509683e0b4643c923c76`, branch
`feat/oia-rules-process-wiring`, clean but with a deleted upstream branch. The
current checkout remains authoritative for this task because it is the selected
working directory. The duplicate is preserved and was not modified or removed.
