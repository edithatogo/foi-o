# FOI-O paper governance

`submission/` is the canonical editable manuscript and bibliography surface;
generated PDFs, source bundles, reviewer reports, and checksums belong under
`reports/paper/<release>/<run_id>/` or another explicitly generated directory.

The paper presents FOI-O as a global, jurisdiction-profiled process/evidence
and verification framework. New Zealand is the origin and mature reference
profile, not the global identity. Every material claim must link to an
immutable evidence/source record, derivability status, and the applicable
version lock. Legal or cross-jurisdiction conclusions remain candidates until
human review and profile-promotion gates are satisfied.

## Required update sequence

1. Lock repository, source-pack, dataset, prompt, tool, model, evaluator, and
   environment identifiers.
2. Reconcile the claim and citation ledgers with Sourceright; retain unresolved
   and ambiguous queues.
3. Build the manuscript and arXiv source bundle reproducibly.
4. Run independent role-isolated review reports, preserving disagreements.
5. Adjudicate findings into a remediation contract and run at most eight
   bounded iterations.
6. Require a score above 995/1000 and every critical gate before a release
   candidate; require human approval before any submission or publication.

AuthenText is a final style and clarity pass only after semantic and citation
integrity. Neither Sourceright nor AuthenText establishes substantive truth,
legal approval, or publication authority.
