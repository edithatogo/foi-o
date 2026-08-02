# Bounded pilot source recovery plan

## Finding

The canonical two-case pilot authorization requires four local roots:

- `/private/tmp/fyi-attachment-snapshot-11872-approved`
- `/private/tmp/foio-governed-reextraction-35076-verified`
- `/private/tmp/foio-bounded-pilot-11872-derived`
- `/private/tmp/foio-bounded-pilot-analysis-v0.2`

A read-only recovery audit on 2026-08-02 found all four roots absent. The
repository and its available local and remote-tracking Git refs contain the
hash-pinned manifests, readiness records, and provenance, but not the source
payloads. No Git object or local storage candidate was found for the missing
directories.

## Recovery options and recommendation

### Option A — restore the original approved bundles (recommended)

Obtain the original owner-readable bundles from their producing workspace or
backup, without changing bytes or provenance. Verify every recorded manifest,
inventory, candidate, and independent-verification hash before placing the
payloads at the authorized paths.

Rationale: this preserves the approved population, rights decision, unit
ordering, and exact authorization. It has the lowest evidentiary risk and
requires no change to the pilot design.

### Option B — recover from a controlled local backup or handoff

Use a local backup, encrypted handoff, or owner-provided archive containing the
same bytes. Treat it as a candidate until all existing hashes, permissions,
record counts, and manifests reproduce exactly.

Rationale: this may be faster than recovering the producing workspace, but a
backup is not evidence by itself. Any mismatch returns to the new-authorization
contingency.

### Option C — create a new bounded source candidate

Capture or assemble replacement material under a separately scoped source,
rights, and population authorization. Produce new manifests and a new
two-case or one-case execution authorization for approval.

Rationale: this is the recovery path only when the original bytes are
irretrievable. It cannot silently repair the existing authorization because it
changes source identity and potentially the evidence population.

### Recommendation and stopping rule

Use Option A first, then Option B. Use Option C only after documenting that the
original bytes are irretrievable. The current track may perform discovery,
hash verification, permission checks, and pre-execution verification only. It
must stop before new capture, source replay, context presentation, analyst
execution, reconciliation, publication, or release.

## Dependency-ordered recovery

## Source-identification and archival procedure

For each missing root, create a recovery ledger entry before copying anything.
The entry must record the candidate location, owner, discovery time, source
type, access method, archive/bundle identifier, expected hash, observed hash,
byte count, permissions, and disposition. The payload must remain owner-only
and outside Git.

### Root-to-source map

| Root | Authoritative source to seek first | Required acceptance evidence |
| --- | --- | --- |
| `fyi-attachment-snapshot-11872-approved` | Original producing workspace or owner-provided local backup of the approved attachment snapshot | Snapshot manifest `0c7cee…5629`, inventory `a0dfea…c171f`, 4 correspondence records, 3 attachments, 13,259,266 bytes, owner-only permissions |
| `foio-governed-reextraction-35076-verified` | Original governed re-extraction workspace or owner-provided handoff bundle | Bundle `c929b3…9b7d`, candidate `90550c…6007`, independent verification `23270c…a9a1`, source-record immutability |
| `foio-bounded-pilot-11872-derived` | Recreated empty quarantine/output directory only after 11872 source verification | Empty before execution, mode `0700`, no derived text copied in during recovery |
| `foio-bounded-pilot-analysis-v0.2` | Recreated empty execution workspace only after both source verifications | Empty before execution, mode `0700`, no contexts or prior analyst outputs |

Ellipses in the table are display abbreviations only; the full hashes in the
canonical readiness and authorization records are authoritative.

### Verification and archival sequence

1. Search the producing checkout, owner-controlled backup, and approved local
   handoff locations in that order. Do not search or retrieve a public dataset
   as a substitute for the approved local payload.
2. For each candidate, perform a read-only inventory and hash computation in a
   temporary quarantine, then compare against the exact recorded pins.
3. Verify ownership and permissions before moving the candidate into its
   authorized root. Reject symlinked, group-readable, world-readable, or
   content-modified candidates unless the authorization explicitly permits the
   condition.
4. Copy or move only a hash-matching candidate into the authorized root using
   an atomic, no-replace operation. Record source and destination hashes and
   the recovery ledger entry.
5. Recreate only the two empty derived/workspace directories with mode `0700`.
6. Run the canonical pre-materialization verifier and preserve its report.
7. If it passes, stop and present the exact recovered-root evidence before any
   execution. If it fails, retain the failure ledger and do not repair by
   altering source bytes.

### Archival record

The restricted-local recovery archive consists of the recovery ledger, source
manifest/inventory, hash report, permissions report, verifier output, and
destination directory metadata. It must not include a second copy of source
payloads in Git, a public dataset, a pull request, or a release bundle.

1. Recover or re-provide the approved request `35076` bundle. Verify manifest
   `d850ca367c2069d7e6d9ac39e8534779d0f64f2b3d708d36f773c0e3a2e271e3`,
   candidate `90550ce084be684ee493e2ce7470cbe0b01dee13b6253c50f91c7de9974d6007`,
   independent verification `23270c27202286e3476f39ccf5df2267cb41641f9cfdf3f1664b8f23e441a9a1`,
   and bundle `c929b312f4b627049b7867e46fa74b08ed8e9a43c35ba866871bead6f8a19b7d`.
2. Recover the approved request `11872` attachment snapshot or obtain a new
   bounded authorization for an equivalent capture. Accept it only if
   snapshot manifest `0c7cee553ca3b01a6416784a1b691df5a6d90159a8f4d55e51a799934f655629`
   and attachment inventory `a0dfea7c979de9760bcf12fee0a321e8e323b4176decd086f2530408da4c171f`
   verify, with four correspondence records, three attachments, and 13,259,266
   attachment bytes.
3. Create the two empty derived/workspace roots with owner-only permissions
   only after both source roots pass verification.
4. Run `verify_pre_materialization` against canonical authorization SHA
   `3d84d40c1b740ae9d2499dcc44f45452cfd24ea8aeb99bc2dcf1aeec54762be3` and the
   resulting clean repository commit.
5. Stop and report any mismatch. Do not substitute a new source, alter the
   approved unit order, or execute the pilot as part of recovery.

## Contingencies

- If `11872` cannot be recovered with the recorded hashes, the approved
  two-case pilot is not executable. Prepare a new one-case `35076` candidate
  and request a fresh exact authorization; do not rewrite the two-case
  authorization.
- If `35076` is recoverable but `11872` is not, no analyst or reconciler runs
  occur under the two-case authorization.
- If both roots are restored but verification fails, preserve the failure
  evidence and stop before context materialization.
- If a backup reproduces the payload but not the recorded permissions, repair
  permissions locally and re-verify; do not alter content or hashes.
- If only one source root is restored, retain it for evidence but do not create
  a partial pilot or infer that the two-case authorization is executable.

## Decision points

No decision is required for Option A or B if the original approved bytes are
available. A decision is required only if both fail: choose whether to stop the
track or authorize Option C with a new source/right/population approval. The
recommended choice in that case is to prepare a one-case `35076` candidate,
because it avoids inventing or reusing the missing `11872` attachment evidence.

## Explicit boundaries

This plan authorizes only local recovery checks and pre-execution verification.
It does not authorize live-origin access, archived replay, new source capture,
publication, redistribution, release, promotion, legal certification, or pilot
execution.
