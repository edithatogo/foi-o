# NZ empirical payload recovery outcome

Status: fail-closed; bounded empirical execution remains blocked.

## Recovery scope

The recovery audit checked the exact approved local roots for the two-case NZ
pilot:

- `/private/tmp/fyi-attachment-snapshot-11872-approved`;
- `/private/tmp/foio-governed-reextraction-35076-verified`;
- `/private/tmp/foio-bounded-pilot-11872-derived`;
- `/private/tmp/foio-bounded-pilot-analysis-v0.2`.

All four roots are absent. The two derived/workspace roots are intentionally
not recreated because their source roots are not verified.

## Read-only sources checked

The audit checked the FOI-O worktree, tracked history and refs, Git notes,
PortableSSD/OneDrive/Downloads/Documents locations, the retained fyi-archive
replay checkout, and fyi-archive Actions artifact metadata. No exact payload
candidate for request `11872` or `35076` was found. No source capture, replay,
origin access, or artifact download was performed for this NZ recovery.

## Required pins

The authoritative readiness records remain the source of truth for the
expected payloads and include:

- 11872 attachment snapshot manifest
  `0c7cee553ca3b01a6416784a1b691df5a6d90159a8f4d55e51a799934f655629`;
- 11872 attachment inventory
  `a0dfea7c979de9760bcf12fee0a321e8e323b4176decd086f2530408da4c171f`;
- 35076 governed bundle
  `c929b312f4b627049b7867e46fa74b08ed8e9a43c35ba866871bead6f8a19b7d`;
- 35076 candidate
  `90550ce084be684ee493e2ce7470cbe0b01dee13b6253c50f91c7de9974d6007`;
- 35076 independent verification
  `23270c27202286e3476f39ccf5df2267cb41641f9cfdf3f1664b8f23e441a9a1`.

These are expected pins, not recovered payloads. They must not be recreated
from fixtures or inferred from derived outputs.

## Disposition

Gate `G-EMP-LOCAL-INPUT-RECOVERY` remains blocked. The existing approved
two-case readiness and execution authorizations are not extended to a
replacement source. The next permitted step is either:

1. owner-provided recovery of the original hash-matching bundles; or
2. a new exact source/right/population approval for a replacement candidate.

No context materialization, analyst execution, reconciliation, empirical
comparison, promotion, publication, redistribution, training, legal
certification, or release occurred.
