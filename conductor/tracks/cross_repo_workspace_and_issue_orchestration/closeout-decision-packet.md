# Closeout decision packet

Date: 2026-08-01

## Recommendation

Keep all four identified workspaces intact and leave this track unarchived.
This is the safest reversible disposition while the checkouts have different
branches, commits, dirty state and upstream configuration.

## Workspace decisions still required

### FOI-O duplicate identity

- Primary candidate: `/Volumes/PortableSSD/GitHub/foi-o`
  - branch: `codex/jurisdiction-completion-roadmap`
  - clean at the closeout recheck
- Duplicate: `/Volumes/PortableSSD/GitHub/foi-o-wiring`
  - branch: `feat/oia-rules-process-wiring`
  - distinct commit history/state

Options:

1. Recommended: retain both and record the wiring checkout as a separately
   preserved workstream.
2. Select one canonical checkout and authorize a separate, recoverable archival
   or relocation procedure for the other.
3. Authorize destructive cleanup of the non-canonical checkout after an
   independent backup and hash verification.

### fyi-archive duplicate identity

- Primary candidate: `/Volumes/PortableSSD/GitHub/fyi-archive`
  - branch: `codex/fyi-archive-type-repair`
  - dirty at the closeout recheck
- Replay checkout: `/Volumes/PortableSSD/GitHub/fyi-archive-au-rtk-replay-30236042144`
  - branch: `codex/au-rtk-replay-30236042144`
  - clean and tracking `origin/main`

Options:

1. Recommended: retain both and preserve the dirty checkout unchanged.
2. Select a canonical checkout and authorize a recoverable archival or
   relocation procedure for the other, without deleting its contents.
3. Authorize destructive cleanup only after backup and hash verification.

## Non-workspace gates

The following remain pending independently of the duplicate decision:

- external issue/project mutation or synchronization;
- publication, submission or release;
- legal or profile promotion.

No option above authorizes those actions. The track can be archived only after
its closeout contract is amended or all listed gates and workspace decisions
are recorded with exact evidence.
