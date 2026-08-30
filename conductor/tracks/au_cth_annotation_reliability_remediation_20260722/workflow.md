# AU-CTH annotation reliability remediation workflow

```mermaid
flowchart TD
  StartEvent[Audit calibration run] --> CodebookApproval{Codebook approved by human?}
  CodebookApproval -- No --> RemediateCodebook[Remediate codebook and contracts]
  RemediateCodebook --> CodebookApproval
  CodebookApproval -- Yes --> HoldoutAcquisition[Acquire rights-eligible authentic AU-CTH records]
  HoldoutAcquisition --> ClusterExclusion[Apply duplicate clustering and exclude calibration clusters]
  ClusterExclusion --> HoldoutApproval{Human approves holdout membership?}
  HoldoutApproval -- No --> ReviewHoldout[Adjust sampling and holdout frame]
  ReviewHoldout --> HoldoutApproval
  HoldoutApproval -- Yes --> BlindedPackets[Generate schema-identical blinded packets]
  BlindedPackets --> ExecAuth{Execution authorization approved?}
  ExecAuth -- No --> BlockedExecution[Hold execution behind gate]
  ExecAuth -- Yes --> DualAnnotation[Run isolated dual annotator roles]
  DualAnnotation --> Adjudication[Adjudicate exact disagreements]
  Adjudication --> ComputeMetrics[Compute agreement, kappa, and extractor metrics]
  ComputeMetrics --> MaturityGate{Human approves maturity claim?}
  MaturityGate -- No --> CandidateStatus[Retain candidate maturity only]
  MaturityGate -- Yes --> EndEvent[Record approved profile maturity]
  CandidateStatus --> EndEvent
  BlockedExecution --> EndEvent
```

Every transition requires predecessor hash pins, codebook version alignment,
and deterministic validator verification. Calibration clusters are strictly excluded
from the fresh holdout. Agent roles remain isolated and unblinded to peer labels.
Maturity claims, legal certification, publication, and gold promotion remain
explicit human gates.
