# AU-CTH subset reliability-computation approval packet

## Proposed operation

Compute restricted-local reliability statistics from the already locked,
automated 385-unit AU-CTH annotation report. This is a descriptive computation
only: it does not authorize extractor scoring, threshold satisfaction, profile
maturity, gold promotion, or publication.

## Pinned inputs

| Item | Value |
| --- | --- |
| Locked annotation report | `22f5850badf02b0730f30fb1221bcc9fa7f6e74ac46338755a6e777eaff1db32` |
| Candidate membership | `f86ed488429009bf3d6a78a7853cca8bb67b8783c728d5ffd255575a9665bda7` |
| Frame | `47115d3d422f0b1d0a2aae856cebd1b8ffca8591e01d42c82d494818c7af2a80` |
| Duplicate clusters | `e4f818d3afbbd4f7bdc1b2f57d94b1da5af73b5887a67e37d528f8813f83f38d` |
| Codebook | `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9` |
| Protocol | `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |

The computation would report raw agreement, Cohen's kappa (or an explicit
undefined reason), exact-span agreement, abstention agreement, 95% cluster
bootstrap intervals, and disagreement counts. With 517 singleton clusters,
the bootstrap resamples units as clusters. It will make no pass/fail or
maturity conclusion.

## Required decision

> I authorize restricted-local reliability computation from locked automated
> annotation report SHA-256
> `22f5850badf02b0730f30fb1221bcc9fa7f6e74ac46338755a6e777eaff1db32`,
> using the pinned 385-unit membership, frame, cluster registry, codebook, and
> protocol recorded in this packet. This authorizes creation and validation of
> a descriptive reliability report only. It does not authorize extractor
> metrics, threshold satisfaction or maturity decisions, gold promotion,
> publication, redistribution, training, legal certification, profile
> promotion, push, pull request, or merge.
