# Paper update and release-candidate workflow

The workflow locks exact inputs, audits claims and sources, runs independent
review roles, and stops at the human publication gate. It is a preparation
workflow, not an autonomous submission path.

```mermaid
flowchart TD
  S([Start]) --> L[Lock repositories sources prompts models]
  L --> C[Build claim and citation ledger]
  C --> R[Run Sourceright and independent review matrix]
  R --> Q{Critical gates and score above 995?}
  Q -- No --> M[Record remediation contract and residual gaps]
  M --> R
  Q -- Yes --> A[Run Authentext editorial pass]
  A --> H{Human approval?}
  H -- No --> X([Hold])
  H -- Yes --> P[Package candidate without submission]
  P --> EndCandidate([Candidate ready])
```
