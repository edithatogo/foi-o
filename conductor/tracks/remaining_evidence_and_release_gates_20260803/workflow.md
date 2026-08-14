# Remaining gates workflow

```mermaid
flowchart TD
  A[Inventory pinned evidence] --> NZ[NZ recover or replace payload]
  A --> AU[Official Australian fixture packets]
  A --> CTH[Verify AU-CTH ledger candidate]
  A --> RM[Prepare public-safe release allow-list]
  AU --> QLD[Queensland registration and terms]
  AU --> MIRROR[Named independent-oracle decision]
  NZ --> RIGHTS{Exact provenance and rights approved?}
  QLD --> RIGHTS
  MIRROR --> RIGHTS
  CTH --> FRAME[Create fresh AU-CTH frame candidate]
  FRAME --> RIGHTS
  RIGHTS -- No --> BLOCK[Record candidate or blocked gate]
  RIGHTS -- Yes --> EXEC{Exact frame and execution approved?}
  EXEC -- No --> BLOCK
  EXEC -- Yes --> EMP[Run only the bounded authorized empirical work]
  RM --> SCOPE{Manifest includes new empirical outputs?}
  SCOPE -- No, public-safe allow-list --> REVIEW[Integrity and rights/publication review]
  SCOPE -- Yes --> EMPREADY{Exact empirical outputs complete and approved?}
  EMP --> EMPREADY
  EMPREADY -- No --> BLOCK
  EMPREADY -- Yes --> REVIEW
  REVIEW --> RELEASE{Exact manifest and one destination approved?}
  RELEASE -- No --> BLOCK
  RELEASE -- Yes --> ACTION[Perform one approved destination action]
  ACTION --> RECEIPT[Verify receipt and destination hashes]
  BLOCK --> END[Recorded outcome]
  RECEIPT --> END
```

The NZ, Australian-source, AU-CTH, and release-preparation lanes may proceed in
parallel, but each joins through its own exact evidence gate. A public-safe
code, schema, documentation, synthetic-example, and provenance-metadata
manifest may proceed without unresolved empirical outputs; an
empirical-inclusive manifest may not. No branch
authorizes live capture, credential use, authentic-content processing,
empirical execution, publication, redistribution, training, legal
certification, or profile promotion by inference.
