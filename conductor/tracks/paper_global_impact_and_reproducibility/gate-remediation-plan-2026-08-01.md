# Track 07 gate-remediation plan

## Current evidence

The local paper-governance audit is deliberately blocked. It reports no
independent reports, no scorecard, all eight critical gates as missing, both
external tools as not run, and publication as unauthorized. This is the
correct fail-closed state.

## Options

### Option A — retain local readiness (recommended)

Keep publication disabled, preserve the current manuscript and evidence
hashes, and prepare review packets without uploading or submitting anything.
This has no external side effects and avoids treating agent output as peer
review or human certification.

### Option B — run the external evidence tools

Authorize bounded Sourceright and Authentext runs against explicitly pinned
inputs and tool revisions. Their outputs must be hash-pinned and independently
reviewed; tool execution alone does not satisfy the human gate.

### Option C — run the review panel

Authorize the listed independent review roles to produce separate reports,
followed by a distinct orchestrator/adjudicator scorecard. Reports remain
candidate review evidence and do not authorize publication or legal claims.

### Option D — authorize submission

Authorize a named destination (arXiv, journal, Zenodo, or other registry),
exact release packet hash, author/rights declarations, and the one submission
operation. This should occur only after Options B and C are complete.

## Recommended sequence and contingencies

1. Retain Option A and generate a hash-pinned review-input inventory.
2. If authorized, run Options B and C in parallel with isolated outputs.
3. Recompute the scorecard from the locked reports; any missing or failed hard
   gate keeps the status `blocked`.
4. If manuscript, citations, rights, or reproducibility inputs change,
   invalidate downstream reports and regenerate them.
5. Only after a passing scorecard and explicit submission authorization should a
   submission packet be handed to the named destination.
6. Archive the track only when the track contract's human gate is explicitly
   satisfied; otherwise retain it as `in_progress`.
