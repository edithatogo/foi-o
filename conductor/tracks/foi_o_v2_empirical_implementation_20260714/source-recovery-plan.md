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

## Dependency-ordered recovery

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

## Explicit boundaries

This plan authorizes only local recovery checks and pre-execution verification.
It does not authorize live-origin access, archived replay, new source capture,
publication, redistribution, release, promotion, legal certification, or pilot
execution.
