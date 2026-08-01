# Track 06 gate-remediation plan

## Current blockers

Repository-owned implementation and validation are complete. The remaining
blockers are explicit human or external gates recorded in `metadata.json` and
`human-gates.yaml`:

1. Publication or release of the implementation or its generated evidence.
2. Legal or profile promotion beyond the bounded, repository-local scope.
3. Registry submission or other external mutation, including pushes, pull
   requests, hosted workflow dispatches, or changes to sibling repositories.

## Options

### Option A — retain restricted-local readiness (recommended)

Keep the track `in_progress`, preserve all hashes and validation evidence, and
wait for a specific gate decision. This has no external side effects and keeps
the implementation reusable for later review.

### Option B — authorize publication/release

Provide an exact artifact or release packet, its SHA-256, target destination,
rights basis, and publication scope. This would permit only the named release
operation; it would not imply legal or profile promotion.

### Option C — authorize legal/profile promotion

Provide an exact profile or registry revision, evidence scope, maturity
criteria, and approval statement. This must remain separate from publication
and cannot be inferred from passing tests.

### Option D — authorize external mutation

Provide the exact repository, branch or PR, commit SHA, operation, and required
checks. Push, PR, merge, workflow dispatch, and sibling-repository changes
remain individually bounded.

## Recommended sequence

1. Retain Option A while no exact gate authorization is supplied.
2. If publication is desired, prepare and review a hash-pinned release packet
   before any upload or release action.
3. If profile or registry promotion is desired, review the exact evidence and
   maturity decision independently of publication.
4. If external mutation is desired, perform the exact authorized operation only
   after local checks pass and record hosted-check results.
5. Archive this track only after all acceptance criteria and any gates included
   in the track contract are explicitly satisfied; otherwise retain it as
   `in_progress`.

## Contingencies

- If a requested artifact lacks rights, provenance, or a stable digest, stop and
  produce a rejection packet rather than publishing it.
- If hosted checks fail, repair only repository-owned failures and rerun the
  required checks; do not bypass protections.
- If evidence changes after approval, invalidate the approval and regenerate
  downstream packets from the new pinned inputs.
- If no gate decision is made, no external action is taken and the validated
  local state remains the authoritative handoff.
