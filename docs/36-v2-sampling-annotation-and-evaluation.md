# Sampling, annotation, and evaluation

Define the population as the public-platform records in a frozen snapshot, not
all FOI requests. Use a stratified probability sample for prevalence and a
separate rare-event enrichment sample for ontology development. Record weights,
inclusion probabilities, duplicate clusters, exclusions, and seeds.

Validation cases receive independent dual annotation and adjudication. Report
raw agreement, label confusion, Krippendorff alpha and/or Gwet AC1/AC2 as
appropriate, disagreement reasons, unknown/not-derivable proportions, and
review effort.

Extractor evaluation uses leakage-safe request-family clusters, a frozen test
set, temporal and jurisdiction holdouts, precision/recall/F1, calibration,
Brier score, abstention/coverage, provenance completeness, and unsafe-inference
rate. Downstream estimates report classification uncertainty.

## Precision and contamination

Sample sizes are justified separately for population estimands, annotation
reliability, extractor evaluation, and inductive coding. Rare-event enrichment
may diagnose uncommon labels but does not estimate prevalence. Inductive coding
uses a recorded information-power/code-stability stopping rule.

The primary test labels should remain sealed or delayed-release until analysis,
thresholds, prompts, and rules are frozen. Public benchmark exposure and model
training-cutoff uncertainty are recorded, and important claims receive a later
prospective temporal refresh.
