# Cross-repository architecture reconciliation

## Confirmed data path

```text
FYI/Alaveteli public records
  -> fyi-cli faithful capture
  -> fyi-archive immutable manifests and archive publication
  -> Hugging Face fyi-archive-nz raw dataset
  -> nlp-policy-nz ontology-pinned candidate extraction
  -> fyi-archive separately versioned derived publication layer
  -> FOI-O evaluation, review, and ontology maturation
```

Alaveteli is an upstream source of public records and workflow intelligence. It
is not an implementation dependency or a target for changes in this programme.

## Repository ownership

| Repository | Immediate role | Explicit boundary |
| --- | --- | --- |
| `fyi-cli` | Capture source records, correspondence, rendered pages, attachments, WARC/WACZ, and source metadata. | Does not own FOI-O semantics or NLP. |
| `fyi-archive` | Orchestrate immutable manifests and mirror publication; later publish a distinct derived dataset. | Raw archive remains immutable; it does not own the NER/NLP implementation. |
| `nlp-policy-nz` | Run ontology-pinned NER/NLP and emit candidate annotations with model, ontology, source-revision, and run provenance. | Outputs are candidates, not gold labels or certified legal findings. |
| `foi-o` | Own ontology, schemas, codebooks, validation, evaluation, and human-promotion boundaries. | Does not fetch source records or publish archive payloads. |
| `fe-reader` | Deferred optional attachment-viewing adapter only. | Technical preview; not an immediate dependency and not required for re-extraction. |

## Re-extraction recommendation

The existing `fyi-archive-nz` snapshot is the immutable input baseline. After
the current FOI-O update is approved, export a versioned extraction contract
from this repository and run a new extraction in `nlp-policy-nz`. Publish the
result through `fyi-archive` under a separate derived path or dataset identity,
never by replacing raw manifests.

Every derived record must retain:

- source dataset revision and source-record identifier;
- content digest and evidence span offsets;
- FOI-O ontology/schema/codebook versions;
- NLP pipeline and model identifiers;
- run identifier, timestamp, parameters, and confidence;
- candidate assertion status and human-review state;
- supersession links to any earlier extraction.

The initial ontology-based output is useful as a baseline and disagreement
source, but it must not be promoted to gold automatically. The re-extraction
should produce a delta report against that baseline and route material label or
span changes to human review.
