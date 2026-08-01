# Plan

- [x] Re-audit live repository, siblings and GitHub.
- [x] Record requirements, risks, decisions and output ledger.
- [x] Implement the read-only workspace doctor, duplicate-clone audit, and issue/project reconciliation.
- [x] Run review and closeout evidence. Current workspace-doctor output and
      duplicate-clone findings are recorded in `review-2026-08-01.md`.
      Verification: 13 focused control tests passed on 2026-08-01;
      workspace doctor, requirements, workflow, repository, Ruff, formatting,
      and diff checks passed.
- [x] Reconcile the output ledger and document the dependency sequence,
      blockers, recommendations and fallbacks in `implementation-report.md`.
- [x] Review Fixes: remove the absolute runtime path from the output ledger;
      keep the runtime-only observation in the review record. [939c689]
- [x] Prepare closeout decision packet covering duplicate workspace identities
      and remaining external gates. [b5268e1]
- [x] Prepare exact external-gate approval wording and record the issue/project
      project-number discrepancy for bounded verification. [65e57ee]
- [x] Verify the linked hosted issue/project state read-only and record the
      result without mutation. [0895ccf]
- [x] Split machine-readable gate status into satisfied verification and
      explicitly pending external/human gates. [ce180e5]
- [ ] Stop at declared human gates.
