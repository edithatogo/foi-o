# Public governance-metadata refactor workflow

```mermaid
flowchart TD
  StartEvent[Inventory candidate paths] --> Classify[Classify governance metadata]
  Classify --> Boundary{Reusable and public-safe?}
  Boundary -- No --> PrivateRef[Retain private artifact and expose opaque pin]
  Boundary -- Yes --> GenericContract[Define generic versioned contract]
  PrivateRef --> Compatibility[Verify historical compatibility]
  GenericContract --> Compatibility
  Compatibility --> Validate[Run contract and repository validation]
  Validate --> ExternalGate{External action authorized?}
  ExternalGate -- No --> Candidate[Retain local candidate]
  ExternalGate -- Yes --> EndEvent[Hand off exact approved candidate]
  Candidate --> EndEvent
```

Raw approvals, request identifiers, local paths, credentials, restricted source
metadata, and receipts never enter the reusable public contract. Historical
evidence remains immutable and is referenced by opaque content pins.
