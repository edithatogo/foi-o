# FOI-O V2 analyst empirical-validation protocol

## Status and relationship to the approved design

This v0.2 candidate reframes the hash-bound v0.1 protocol in
`docs/41-v2-sampling-and-annotation-protocol.md`. It preserves that approved
artifact unchanged. This successor requires its own exact approval before
authentic execution.

“Analyst” and “reconciler” are roles. A role actor may be a human or an
automated agent. Every actor must have a distinct identity and recorded actor
class, runtime or model identity, configuration, prompt or instruction digest,
and execution provenance. Agent-produced outputs may support bounded empirical
evidence when they derive from authentic governed inputs and pass the verifier;
they are not thereby human-reviewed, legally certified, or gold.

## Sampling and claim scope

A bounded authentic sample is sufficient for pilot validation or another claim
expressly limited to the sampled units. It is not evidence of archive-wide
prevalence or performance. A population estimate additionally requires the
predeclared probability design, inclusion probabilities, weights, clustering,
and sample-size justification specified by the v0.1 design.

The already completed 11-unit fixture run is synthetic contract validation. It
cannot be relabelled as authentic empirical validation. Requests `11872` and
`35076` are authentic bounded reproducibility cases, but two purposively chosen
requests are suitable only for case-level or pilot claims unless a broader
sampling design is frozen.

## Independent analysis and reconciliation

1. Freeze the rights-eligible authentic sample and all source spans before any
   analyst sees a unit.
2. Run two distinct analysts independently. Neither may see the other output,
   the extractor candidate label, or candidate confidence before both complete
   sets are content-hash locked.
3. Record actor provenance, unit and source digests, codebook revision, label,
   exact UTF-8 character half-open `[start, end)` span, uncertainty, abstention,
   rationale, timestamps, and
   lock digest for every analysis.
4. Give a distinct reconciler only the authentic source and both locked sets.
   Preserve both original analyses and record every resolved or unresolved
   decision with rationale and immutable references.
5. Compute reliability and extractor metrics from the locked authentic bundle.
   Report abstentions, unresolved units, missingness, denominators, adverse
   results, and uncertainty without suppression.

## Claim and promotion boundaries

- `empirical_evidence` may be true for verified data-derived agent analysis.
- `human_reviewed` must remain false unless a human performed the defined review.
- `gold` and legal certification require separate exact human approval.
- Publication, redistribution, training, release, dataset publication, and
  paper updates remain separately gated.

## Execution gate

Before execution, commit and verify an exact authorization binding the source
population, frozen sample, codebook, sampling configuration, two analyst actors,
one reconciler actor, all runtime provenance, claim scope, and prohibitions.
