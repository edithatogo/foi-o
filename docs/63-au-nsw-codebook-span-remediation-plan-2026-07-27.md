# AU-NSW codebook and span-remediation plan

The named decision retains `foi-o-au-nsw` at candidate status and opens this
remediation queue. Existing annotations, adjudications, and reliability
reports are immutable evidence and must not be overwritten.

## Pinned adverse evidence

- Reliability report: `7bc2469dadf622b9182af6b33eb3fa8dd6cabe9350040b75f46fce287770774f`.
- Locked annotation report: `74125814a8d3da0d161db777e8884847fa5c2bbe1c4f634e8aab228125ee6455`.
- Disagreement queue: 70 units, adjudicated by the distinct automated role.
- Exact-span agreement: 30/100.

## Remediation work items

1. Audit all 70 disagreement records by dimension: label, span, and
   abstention. Preserve each original annotation and adjudication.
2. Separate label disagreement from span-boundary disagreement; do not count
   a span-boundary correction as evidence that the ontology label was wrong.
3. Review the NSW-specific `observed`, `inferred`, `candidate`, and `unknown`
   rules for GIPA wording, informal enquiries, formal applications, and
   references to non-GIPA information-access pathways.
4. Define a shortest-sufficient-span calibration rule with positive and
   negative examples, then pin a new codebook revision if changes are needed.
5. Run a fresh, separately approved holdout annotation after the revised
   codebook exists. Do not reuse the current 100-unit labels as fresh evidence.
6. Recompute reliability only after the fresh holdout is locked and separately
   authorized.

No item authorizes extractor metrics, gold promotion, publication,
redistribution, training, legal certification, profile promotion, push, pull
request, or merge.
