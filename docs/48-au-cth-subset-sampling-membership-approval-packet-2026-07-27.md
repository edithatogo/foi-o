# AU-CTH subset sampling-membership approval packet

## Proposed operation

Run the pre-registered deterministic probability-sampling procedure once over
the frozen restricted-local 517-record AU-CTH HTML subset, then produce and
validate a non-annotation candidate membership manifest. This does not execute
annotation or create labels.

## Pinned inputs

| Item | Value |
| --- | --- |
| Frozen subset frame | `47115d3d422f0b1d0a2aae856cebd1b8ffca8591e01d42c82d494818c7af2a80` |
| Duplicate-cluster registry | `e4f818d3afbbd4f7bdc1b2f57d94b1da5af73b5887a67e37d528f8813f83f38d` |
| Frame size | 517 units; 517 singleton clusters |
| Seed | `20260721` |
| Sampling protocol | `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |
| Preregistration | `4264bcad4b2b83ffe6df312626f7b3ea285f9b19a1b40aa0952b4358c08d9118` |
| Probability sample target | 385 units, without replacement |
| Allocation | proportional by available strata; largest-remainder rounding |
| Replacement | prohibited after draw |

The candidate membership output would record all inclusion probabilities,
weights, excluded 132 units, seed, ordering digest, and the inability to make
population-wide inferences from this retained-HTML subset.

## Required decision

> I authorize one local deterministic probability-sampling run from frozen
> AU-CTH subset-frame SHA-256
> `47115d3d422f0b1d0a2aae856cebd1b8ffca8591e01d42c82d494818c7af2a80`,
> using duplicate-cluster registry SHA-256
> `e4f818d3afbbd4f7bdc1b2f57d94b1da5af73b5887a67e37d528f8813f83f38d`,
> seed `20260721`, and the stated 385-unit no-replacement design. This
> authorizes creation and validation of a candidate sampling-membership
> manifest only. It does not authorize annotation, adjudication, extractor
> metrics, population-wide inference, publication, redistribution, training,
> legal certification, profile promotion, push, pull request, or merge.
