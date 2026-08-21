# Legacy evidence-ledger migration plan

Status: planned; fail-closed. This plan does not rewrite the existing ledger.

## Problem

The first two records in `evidence.jsonl` use a historical event-shaped form,
while later records use the canonical hash-chain form. A canonical append helper
must not silently append to an unverifiable mixed-prefix chain.

## Migration sequence

1. Preserve and hash the current ledger as a historical input; never edit it.
2. Produce a machine-readable reconciliation report identifying the exact legacy
   prefix, the first canonical entry, and any unverifiable chain boundary.
3. Introduce a distinct successor ledger only after it declares its predecessor
   artifact hash and a migration/reconciliation status.
4. Require every new successor entry to use the canonical schema and hash chain.
5. Leave validation fail-closed when the historical prefix or declared handoff
   does not match its pinned bytes.

## Boundary

No historical event is reinterpreted, re-dated, re-hashed, deleted, or treated
as new evidence. The migration can improve future appendability but cannot cure
missing source, rights, empirical, publication, or approval gates.

## Validation contract

- Check canonical JSON-line parsing and required fields for every successor entry.
- Verify the frozen legacy artifact hash and declared handoff reference.
- Reject direct appends to a mixed-prefix ledger and a mismatched predecessor.
- Run Conductor full validation and focused positive/negative regression tests.

## Completion condition

The migration is complete only when the historical ledger remains byte-identical,
a separately named successor validates, and no future automation can append to
the mixed historical file.
