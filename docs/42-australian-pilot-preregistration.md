# Australian Commonwealth and NSW pilot pre-registration candidate

Status: candidate contract only. This document fixes the analysis choices that
must be approved before any authentic source population is sampled. It is not
an archive manifest, an annotation packet, a gold set, or evidence of profile
promotion.

## Scope and unit

The two populations are separate and must never be pooled:

- `AU-CTH` / `FOI`: public, request-linked platform records whose jurisdiction
  and regime can be established from the pinned capture metadata.
- `AU-NSW` / `GIPA`: public, request-linked platform records whose jurisdiction
  and regime can be established from the pinned capture metadata.

The primary unit is one request-linked candidate assertion with one immutable
source span. A request may contribute multiple assertions, but each assertion
retains its request-family and duplicate-cluster identifiers. Legislation and
platform records are evidence sources; this study does not label legal
correctness or infer a legal outcome from platform state.

## Inclusion and exclusions

Include a unit only when it has a stable source identifier, a retrievable or
rights-approved source reference, a jurisdiction/regime assignment, and a
UTF-8 text span or an explicit `missing_evidence` disposition.

Exclude before sampling, recording one reason per excluded record:

1. `wrong_jurisdiction_or_regime` — not AU-CTH/FOI or AU-NSW/GIPA;
2. `outside_time_window` — outside the frozen capture interval;
3. `non_public_or_access_restricted` — access requires credentials or bypass;
4. `rights_ineligible` — redistribution or annotation rights are absent;
5. `unresolved_identity` — request/source identity cannot be established;
6. `malformed_or_unreadable` — the preserved artifact cannot be decoded;
7. `duplicate_cluster_representative` — retained only as a cluster member;
8. `non_request_material` — navigation, advertisements, or unrelated content.

No inaccessible or excluded unit is silently replaced after the frame is
frozen. Exclusions remain in the frame ledger with source digest and reason.

## Stratification and sample sizes

The probability sample uses proportional allocation across jurisdiction,
calendar year, platform/provider, and request-state family, with a minimum of
25 units per non-empty stratum. The target is **385 eligible units per
jurisdiction**: the conservative Wald planning value for a proportion of .50,
95% confidence, and ±5 percentage points (`1.96^2*.25/.05^2 = 384.16`,
rounded up). If a finite population is smaller than 385, use a census and
record the finite-population correction. Sampling weights are the inverse
inclusion probabilities.

Separate from that estimand sample, draw **100 paired annotation units per
jurisdiction** from the probability frame, allocated proportionally by the
same strata and rounded by largest remainder. This provides a fixed review
workload and a reliability estimate; it is not a claim that every label has
power for a rare prevalence. Add a separate rare-event enrichment of at most
50 units per jurisdiction for ontology development; enrichment is excluded
from prevalence estimates and extractor headline metrics.

The frozen random seed is **20260721**. Use a version-pinned deterministic
PRNG, sort candidate rows by canonical unit digest before sampling, and record
the PRNG/library version in the sample manifest.

## Duplicate and leakage control

Canonicalize Unicode (NFC), lowercase, collapse whitespace, remove tracking
parameters from URLs, and hash the normalized request title plus body,
provider, and jurisdiction. Exact canonical hashes form a cluster. Near
duplicates form a cluster when character 5-gram MinHash Jaccard is at least
0.90 or normalized Levenshtein similarity is at least 0.92, provided the same
request-family key is present. Attachments use their byte SHA-256 and parent
request key. Manual merges require a reason and reviewer identity.

Clusters are atomic for exploration, development, validation, annotation, and
test splits. A cluster may occur in the sequential annotation/adjudication
stages, but never in two analytical partitions.

## Codebook revision candidate

Codebook ID: `foio-au-pilot-assertion-v0.1.0`.

Each assertion receives exactly one primary label, one optional UTF-8
half-open span, an abstention flag, and a reason where abstaining. Labels:

| Label | Positive rule | Negative rule |
| --- | --- | --- |
| `observed` | The source explicitly states or displays the asserted event/state. | Do not use for interpretation, implication, or a second-hand summary. |
| `inferred` | The assertion follows mechanically from explicit source facts, with the facts and derivation recorded. | Do not use where the source is ambiguous or a legal conclusion is required. |
| `candidate` | The text supports a possible ontology mapping, but source or temporal evidence is incomplete. | Do not use when the mapping is contradicted or unsupported. |
| `unknown` | The assertion cannot be decided from the supplied evidence. | Do not use as a substitute for a negative observation. |

Annotators must abstain rather than guess, using only
`missing_evidence`, `insufficient_evidence`, `out_of_scope`, or `other`.
Adjudication is triggered by any label, span, or abstention disagreement.
The codebook is not approved until a named human approver and timestamp are
recorded, and its revision hash is pinned in the sample and annotation
manifests.

## Reliability and extractor thresholds

Report raw agreement and Cohen's kappa for each jurisdiction and label family,
with two-sided 95% cluster-bootstrap intervals (10,000 replicates, resampling
duplicate clusters). Report kappa as undefined with the reason when a marginal
is constant. The minimum reliability gate is raw agreement >= 0.80 and kappa
>= 0.60 for every primary label family; any failure keeps the profile at
candidate maturity and opens a disagreement queue.

For spans, report exact-span agreement and overlap F1 using an intersection
over union threshold of 0.50. For the ontology-pinned extractor, report
precision, recall, F1, abstention/coverage, provenance completeness, and
unsafe-inference rate against the adjudicated set. The minimum extractor gate
is precision >= 0.85, recall >= 0.75, F1 >= 0.80, provenance completeness
>= 0.95, and unsafe-inference rate <= 0.01 on the probability sample. These
are thresholds for a maturity decision, not automatic promotion criteria.

The final packet must include confusion tables, denominators, missingness,
abstentions, unresolved disagreements, per-stratum and per-cluster queues,
confidence intervals, and a human maturity decision. No placeholder,
synthetic, repeated-hash, or AI-proposed fixture may enter those metrics.

## Blinded packet generation

Once an authentic frozen frame and approved codebook exist, generate the two
independent packets with:

```text
python scripts/build_australian_blinded_packets.py \
  --frame <frozen-authentic-frame.json> \
  --codebook <approved-codebook.json> \
  --output-a <annotator-a.packet.json> \
  --output-b <annotator-b.packet.json>
```

The builder rejects non-authentic frames, rights-ineligible units, digest
mismatches, missing unit text, and any input containing extractor candidate
labels or confidence. It emits the same deterministically shuffled units to
two role-specific packets with peer and extractor blinding asserted.
