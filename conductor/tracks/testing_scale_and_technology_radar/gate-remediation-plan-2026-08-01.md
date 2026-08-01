# Testing-scale and technology-radar gate-remediation plan

## Current blockers

The local testing and radar controls pass. Promotion remains blocked until a
technology has named-consumer benchmark evidence, independent review, and an
explicit human decision. Publication, profile promotion, and external mutation
are separate gates.

## Options

### Option A — retain the current radar rings (recommended)

Keep adopt/trial/assess/hold assignments unchanged and preserve the current
default paths. This avoids unverified technology migration and has no external
side effects.

### Option B — run a bounded benchmark

Select one named consumer and one candidate technology, pin revisions and
inputs, define quality/performance thresholds, and produce a local comparison
packet. A benchmark is evidence only; it does not promote the technology.

### Option C — authorize promotion

Approve the exact technology, benchmark packet, independent review, affected
default path, rollback plan, and promotion revision. This must remain separate
from publication.

## Recommended sequence and contingencies

1. Retain Option A while no benchmark target is approved.
2. If evaluation is desired, run Option B in an isolated local output area.
3. Re-run repository quality and consumer-contract checks after any change.
4. Promote only after independent review and the human gate pass.
5. If benchmarks regress, keep the technology in its current ring and record a
   rejection or hold decision.
6. Archive only after all track acceptance criteria and human gates are
   complete.
