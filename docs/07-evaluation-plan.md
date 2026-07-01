# Evaluation plan

## Evaluation principle

This project should be empirical. The ontology should grow from observed public records, guidance, legislation, and reporting data rather than abstract legal modelling alone.

## Gold sets

Create small, manually reviewed gold sets before scaling extraction:

| Gold set | Size | Purpose |
|---|---:|---|
| State mapping | 100 requests | Evaluate source-state to normalised-state mapping. |
| Timeline extraction | 50 requests | Extract received, acknowledgement, extension, transfer, decision, release dates. |
| Outcome extraction | 50 requests | Extract release/refusal/no-information/withdrawal/partial outcomes. |
| Legal issue spotting | 50 decisions | Identify candidate withholding grounds and public-interest discussion without treating the model as decisive. |
| Attachment profile | 100 attachments | Classify content type, record type, OCR need, redaction presence. |

## Metrics

- exact-match for source metadata;
- precision/recall/F1 for event extraction;
- calibration curves for confidence scores;
- false-positive rate for legal issue flags;
- percentage of outputs with complete provenance;
- rate of unsafe decision-like outputs caught by validation;
- reporting-metric derivability from public data vs agency-internal data.

## Baseline methods

Compare:

1. deterministic source parsing;
2. rules + regex over correspondence;
3. small supervised classifiers after gold-set creation;
4. LLM extraction with structured outputs;
5. ensemble extraction with abstention.

LLM outputs should be candidates, not ground truth.
