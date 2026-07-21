# FOI-O V2 sampling and annotation protocol

## Status and boundary

This is a candidate protocol for named-human approval. It does not freeze a
sample, appoint reviewers, create labels, adjudicate disagreements, calculate
reliability, or authorize empirical claims. Execution requires a rights-approved
source population and an approved role packet.

## Source population and units

1. Pin the complete eligible source-population manifest by repository revision
   and SHA-256 before drawing any unit.
2. Exclude records outside the approved rights scope before sampling and record
   every exclusion reason.
3. Define the primary unit as one request-linked candidate assertion with its
   immutable source span and provenance. Preserve request identifiers only as
   governed linkage keys.
4. Assign duplicate or near-duplicate requests to immutable clusters before
   splitting or sampling. A cluster must not cross exploration, development,
   validation, or sealed evaluation/test partitions. The same cluster identity
   follows a unit through annotation and adjudication; those are sequential
   stages, not mutually exclusive partitions.

## Sampling design

- Maintain a probability sample for population estimands and a separate
  rare-event enrichment sample for ontology development.
- Pre-register the random seed, strata, inclusion probabilities, sampling
  weights, cluster rule, exclusion rule, and sample-size justification.
- Freeze membership once. Do not replace inaccessible units after freeze;
  retain them with an explicit accessibility disposition.
- Do not combine enriched and probability samples into prevalence estimates.
- The current one-record request `35076` artifact is a reproducibility case,
  not an empirical sample or sample-size justification.

## Independent annotation

1. Appoint two distinct human annotators and one distinct adjudicator. None may
   be represented by an automated agent or model.
2. Annotators work independently and cannot see each other's labels.
3. For extractor evaluation, annotators review source evidence without seeing
   the extractor candidate label or confidence. Candidate identifiers may be
   revealed only after independent labels are locked.
4. Each annotation records reviewer identity, timestamp, unit digest, codebook
   version, label, exact span, uncertainty, abstention, and notes.
5. Missing evidence or inability to decide produces abstention, not an inferred
   label.

## Adjudication

- Lock both annotation sets before adjudication.
- The adjudicator reviews the source and both independent annotations, records
  a reasoned decision or unresolved status, and never silently overwrites an
  annotation.
- Every change retains the two original labels, adjudicated label, rationale,
  adjudicator identity, timestamp, and artifact hashes.
- Only adjudicated, rights-eligible units may enter an empirical evaluation
  set. Gold promotion remains a separate named-human decision.

## Reliability and evaluation

Use UTF-8 character offsets with half-open `[start, end)` spans. Calculate all
denominators explicitly: report missing evidence and abstentions separately,
exclude unresolved units from extractor scoring but include them in coverage
and unresolved-rate reporting, and never convert abstentions to negative
labels. Use two-sided 95% cluster-bootstrap confidence intervals, resampling
duplicate clusters and applying probability weights only to the probability
sample. When kappa is undefined because a marginal is constant, report raw
agreement and the undefined reason rather than substituting a value. Match
extractor spans by exact offsets and overlap F1, using the pre-registered label
taxonomy and threshold without post-freeze tuning.

Report these pre-specified outputs without suppressing zero or adverse results:

- unit and label counts, missingness, abstentions, and class prevalence;
- raw agreement and Cohen's kappa for nominal labels, with confidence intervals;
- exact-span agreement and overlap F1 for span annotations;
- disagreement counts by label, stratum, year, state, and duplicate cluster;
- adjudication rate and unresolved rate;
- extractor precision, recall, and F1 against the adjudicated set, with
  confidence intervals and probability-sample weights where applicable.

Reliability statistics must be calculated from authentic locked annotation
records. Contract fixtures, AI-proposed labels, repeated placeholder hashes,
or the one-record reproducibility case are not substitutes.

## Required approvals before execution

- named protocol approver and approval timestamp;
- two distinct annotator identifiers;
- one distinct adjudicator identifier;
- rights-approved source-population manifest;
- approved codebook revision;
- approved sample-size justification and frozen sampling configuration.
