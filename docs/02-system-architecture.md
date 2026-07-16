# System architecture

FOI-O is the semantic and jurisdiction-contract layer in a multi-repository
programme. FOI-O NZ is its currently implemented jurisdiction profile. Capture,
archiving, OCR, extraction, rules, and programme conformance remain separate so
that their provenance and approval boundaries are inspectable.

```mermaid
flowchart LR
  A[FYI / Alaveteli public records] --> B[fyi-cli capture and deltas]
  B --> C[fyi-archive manifests and provenance]
  C --> D[Hugging Face / Zenodo / OSF]
  C --> E[foi-process document evidence and OCR]
  E --> F[nlp-policy-nz candidate extraction]
  G[legislation and official guidance] --> H[FOI-O core and jurisdiction profiles]
  F --> H
  H --> I[JSON Schema / OWL / SKOS / SHACL]
  H --> J[rulespec-nz deterministic rules]
  I --> K[Agent-facing contracts]
  J --> K
  K --> L[Human-supervised workflows]
  M[rac-conformance] -. programme synchronization .-> B
  M -.-> L
```

## Layers

### 1. Source layer

Public sources include FYI.org.nz request pages, Alaveteli metadata,
attachments, versioned legislation packs, public guidance, PSC statistics, and
Ombudsman complaint data. Alaveteli is a source of workflow intelligence and
public metadata, not an implementation dependency for FOI-O governance.

### 2. Archive layer

`fyi-cli` captures source and delta inputs. `fyi-archive` preserves source
material, produces manifests and publication packages, and sends versioned
datasets to Hugging Face and preservation services. This layer prioritises
fidelity over interpretation.

### 3. Semantic layer

`foi-process` supplies document-evidence and OCR views. `nlp-policy-nz` evaluates
review-bounded candidate extraction. FOI-O maps accepted evidence into events,
states, controlled vocabularies, legal references, and validation constraints;
`rulespec-nz` supplies deterministic NZ rules. Candidate extraction is never
equivalent to profile promotion.

### 4. Agent layer

Agents consume typed resources and tools. Their outputs remain preparatory unless a human with authority certifies a decision-like event.

Australian Commonwealth and NSW adapters are pilot consumers of the same
contract. They remain disabled or candidate-only until immutable source and
model pins, rights-reviewed heldout data, independent annotation and
adjudication, empirical metrics, and explicit human promotion are recorded.

### 5. Reporting and evaluation layer

The event log should support:

- state mapping evaluation;
- extraction accuracy measurement;
- statutory clock calculation tests;
- reporting-metric generation;
- public/private data boundary checks;
- audit and reproducibility reports.
