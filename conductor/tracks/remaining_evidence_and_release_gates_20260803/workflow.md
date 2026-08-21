# Remaining gates workflow

```mermaid
flowchart TD
  A[Inventory pinned evidence] --> NZ[NZ recover or replace payload]
  A --> AU[Official Australian fixture packets]
  A --> CTH[Verify AU-CTH ledger candidate]
  A --> RM[Prepare public-safe release allow-list]
  NZ --> NZP[Agent advisory panel]
  NZP --> NZD{Sole maintainer approves NZ scope?}
  NZD -- No --> BLOCK[Record candidate or blocked gate]
  NZD -- Yes --> NZEMP[Run only the bounded authorized NZ work]
  AU --> AUP[Agent advisory panel]
  AUP --> AUD{Sole maintainer approves official fixture scope?}
  AUD -- No --> BLOCK
  AUD -- Yes --> QLD[Queensland registration and terms]
  QLD --> QLDP[Agent advisory panel]
  QLDP --> QLDD{Sole maintainer approves QLD scope?}
  QLDD -- No --> BLOCK
  AUD -- Yes --> MIRROR[Named mirror-comparator decision]
  MIRROR --> MP[Agent advisory panel]
  MP --> MD{Sole maintainer approves mirror scope?}
  MD -- No --> BLOCK
  CTH --> FRAME[Prepare fresh AU-CTH frame candidate]
  FRAME --> CTHP[Agent advisory panel]
  CTHP --> CTHD{Sole maintainer approves frame and execution?}
  CTHD -- No --> BLOCK
  CTHD -- Yes --> CTHEMP[Run only the bounded authorized AU-CTH work]
  RM --> SCOPE{Manifest includes new empirical outputs?}
  SCOPE -- No, public-safe allow-list --> REVIEW[Integrity and rights/publication review]
  SCOPE -- Yes --> EMPREADY{Exact empirical outputs approved?}
  NZEMP --> EMPREADY
  CTHEMP --> EMPREADY
  EMPREADY -- No --> BLOCK
  EMPREADY -- Yes --> REVIEW
  REVIEW --> RP[Agent advisory panel]
  RP --> RELEASE{Sole maintainer approves exact destination?}
  RELEASE -- No --> BLOCK
  RELEASE -- Yes --> ACTION[Perform one approved destination action]
  ACTION --> RECEIPT[Verify receipt and destination hashes]
  BLOCK --> END[Recorded outcome]
  QLDD -- Yes --> END
  MD -- Yes --> END
  RECEIPT --> END
```

The NZ, Australian-source, AU-CTH, and release-preparation lanes may proceed in
parallel. Each lane enters its own agent advisory panel and sole-maintainer
decision; unrelated lanes do not become prerequisites by implication. A public-safe
code, schema, documentation, synthetic-example, and provenance-metadata
manifest may proceed without unresolved empirical outputs; an
empirical-inclusive manifest may not. No branch
authorizes live capture, credential use, authentic-content processing,
empirical execution, publication, redistribution, training, legal
certification, or profile promotion by inference.
