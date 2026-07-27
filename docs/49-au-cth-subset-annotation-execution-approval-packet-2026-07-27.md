# AU-CTH subset annotation-execution approval packet

## Proposed operation

Generate two blinded annotation packets and execute two isolated automated
annotator roles plus one distinct automated adjudicator role over the exact
385-unit AU-CTH retained-HTML candidate membership. This is bounded local
evaluation only and does not promote any gold set or profile.

## Pinned inputs

| Item | Value |
| --- | --- |
| Frozen subset frame | `47115d3d422f0b1d0a2aae856cebd1b8ffca8591e01d42c82d494818c7af2a80` |
| Duplicate clusters | `e4f818d3afbbd4f7bdc1b2f57d94b1da5af73b5887a67e37d528f8813f83f38d` |
| Candidate membership | `f86ed488429009bf3d6a78a7853cca8bb67b8783c728d5ffd255575a9665bda7` |
| Units | 385, sampled without replacement from the 517-record retained-HTML subset |
| Codebook | `foio-au-pilot-assertion-v0.2.0`, SHA-256 `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9` |
| Protocol | `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |

Roles must be isolated: Annotator A and Annotator B cannot view each other's
answers or extractor outputs; the adjudicator may view both only after they are
locked. Outputs remain restricted-local and preserve original labels,
provenance, abstentions, disagreements, and adjudication rationale.

## Required decision

> I authorize two independent automated annotator roles and one distinct
> automated adjudicator role to generate blinded packets and perform bounded
> annotation and adjudication only on the 385-unit AU-CTH candidate membership
> SHA-256 `f86ed488429009bf3d6a78a7853cca8bb67b8783c728d5ffd255575a9665bda7`,
> under codebook `foio-au-pilot-assertion-v0.2.0` SHA-256
> `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9` and
> protocol SHA-256 `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf`.
> This authorizes restricted-local agreement and disagreement-queue
> computation only. It does not authorize extractor metrics, gold promotion,
> publication, redistribution, training, legal certification, profile
> promotion, push, pull request, or merge.
