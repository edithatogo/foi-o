# AU-NSW remediation and fresh-holdout approval packet

## Remediation basis

The locked 100-unit run produced 24 label disagreements, 70 span
disagreements, and 12 abstention disagreements. Annotator A used labels
observed/unknown/candidate at counts 70/24/6; annotator B used
observed/unknown/candidate at counts 46/36/18. These counts are diagnostic
only and do not alter the locked report.

## Proposed revision

Use the NSW-specific codebook candidate
`examples/v2/au-nsw-assertion-codebook.v0.2.1.pending.json` with its own hash.
The revision narrows `observed` to explicit GIPA/governing-act text, separates
generic access language into `candidate` or `unknown`, and restricts spans to
the shortest governing-act context. It supersedes v0.2.0 only after approval.

## Fresh holdout design

- Population: the immutable 115-unit AU-NSW frame.
- Existing 100-unit membership and all prior labels: excluded from the fresh
  holdout draw to prevent reuse.
- Fresh holdout: deterministic 15-unit no-replacement complement, sorted by
  text SHA-256, seed `20260721`, singleton duplicate clusters.
- Roles: two independent automated annotators and one distinct adjudicator.
- Outputs: blinded packets, locked annotations, disagreement queue, and
  adjudications only.
- Reliability: the existing registered thresholds and 10,000-replicate
  singleton-cluster bootstrap; no threshold relaxation or post-hoc tuning.

This is a proposed design. It does not create membership, packets, labels,
metrics, or promotion evidence.

## Required approvals

> I approve the NSW codebook candidate
> `examples/v2/au-nsw-assertion-codebook.v0.2.1.pending.json`, SHA-256
> `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6`, and authorize its use for a fresh 15-unit AU-NSW holdout
> drawn from the immutable 115-unit frame, excluding the prior 100-unit
> membership. I authorize deterministic membership creation only at this
> stage, using seed `20260721` and the stated singleton-cluster rules. This
> does not authorize packet generation, annotation, adjudication, extractor
> metrics, publication, redistribution, training, promotion, push, pull
> request, or merge.
