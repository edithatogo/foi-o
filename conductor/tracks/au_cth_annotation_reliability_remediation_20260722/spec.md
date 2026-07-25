# Specification: AU-CTH annotation reliability remediation

## Overview

Repair the evidence chain and annotation contract exposed by the nine-unit
AU-CTH calibration run, then evaluate reliability on a fresh, frozen holdout.

## Authoritative inputs

- `docs/41-v2-sampling-and-annotation-protocol.md`
- `docs/42-australian-pilot-preregistration.md`
- `docs/44-au-cth-annotation-outcome-and-remediation.md`
- `examples/v2/au-cth-fulltext-sample-freeze.approved.json`
- `examples/v2/au-cth-annotation-execution.approved.json`
- `examples/v2/au-cth-annotation-metrics.pending.json`
- AU-CTH full-text capture run `29922684296`, artifact SHA-256
  `5f5d4114136c0f2927287ae9edd8ca55b6648431c150dc02c334f581fb7efb48`

## Requirements

1. Preserve the existing run as calibration-only evidence with immutable
   hashes, role provenance, and no raw source text committed to Git.
2. Replace ephemeral and synthetic provenance with committed schemas, an exact
   codebook, a real repository revision, and cross-artifact validators.
3. Specify the assertion, evidence window, jurisdiction rule, span boundaries,
   abstention/null encoding, and adjudication rules with positive and negative
   fixtures.
4. Use one canonical annotation-output schema for both annotators.
5. Keep seed `20260721`, duplicate clustering, exclusions, and registered
   reliability thresholds unchanged unless separately preregistered and
   approved before seeing fresh holdout labels.
6. Treat the nine existing cases as calibration-only. Reliability and
   extractor maturity metrics require a fresh frozen holdout.
7. Compute confusion tables, raw agreement, Cohen's kappa, span exact match,
   span overlap F1, abstention agreement, bootstrap intervals, and explicit
   denominators through deterministic code.
8. Keep gold promotion, publication, redistribution, training, release, legal
   certification, and maturity promotion behind separate human gates.

## Acceptance criteria

- All calibration artifacts are durably inventoried by SHA-256 and validated;
  no governed manifest points at `/tmp`.
- The approved codebook has a real Git revision and exact content hash.
- Positive and negative contract tests reject mismatched hashes, roles,
  schemas, unit membership, invalid spans, and peer-label leakage.
- A fresh authentic holdout is frozen without any calibration cluster.
- Two role-isolated outputs validate against the same schema and account for
  every holdout unit exactly once.
- Metrics are recomputed by repository code; primary-label agreement is at
  least 0.80 and kappa at least 0.60 for every registered family, or maturity
  remains candidate.
- The final packet distinguishes automated-agent evidence from human review
  and records a human maturity decision separately.
- The remediation workflow has Markdown/Mermaid and BPMN 2.0 representations.

## External gates

- Rights approval for any additional authentic source records.
- Hash-bound approval of the revised codebook and fresh holdout membership.
- Exact authorization for the fresh annotation run.
- Human maturity decision after verified metrics.

## Out of scope

- Relaxing thresholds in response to this result.
- Treating the nine calibration cases as an independent holdout.
- Publishing or redistributing source text or labels.
- Certifying legal correctness or promoting a profile automatically.

