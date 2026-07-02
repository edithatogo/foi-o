# OIA process profile v0.1

The first FOI-O NZ profile should be event-centred rather than document-centred.

## Lifecycle states

The normalised state vocabulary should start small:

```text
observed
submitted
awaiting_response
awaiting_clarification
scope_amended
transfer_assessed
transferred
search_planned
searching
records_identified
consultation_required
consultation_in_progress
extension_notified
charge_assessed
decision_drafted
human_decision_required
decision_certified
decision_communicated
released_in_full
released_in_part
refused
information_not_held
withdrawn
overdue
complaint_observed
closed
published
unknown
```

Source states from FYI/Alaveteli must be preserved separately. A source state such as `successful` may map to `released_in_full`, `released_in_part`, or `decision_communicated` depending on correspondence evidence. A source state should never be treated as a final legal conclusion without evidence.

## Request profile JSON-LD

Request profiles are normalised source records, not legal determinations. The JSON-LD example at `examples/request-record.jsonld` must validate against `schemas/json/request-profile.schema.json` and parse as RDF using `contexts/foi-o-nz.context.jsonld`.

The request profile contract keeps source and derived values separate:

| Field | Meaning |
|---|---|
| `source_state` | The raw FYI/Alaveteli state label, preserved unchanged. |
| `normalised_state` | The current FOI-O NZ lifecycle state produced by deterministic mapping. |
| `state_mapping` | Mapping method, confidence, notes, and evidence identifiers. |
| `source_provenance` | Input path when repo-local, source record id, raw state field/value, mapping basis, mapping confidence, and evidence id. |

Current generated profile states use the implementation vocabulary such as `ReleasedInFull`, `ReleasedInPart`, `Refused`, `NoDocumentsFound`, `Received`, and `AwaitingClarification`. Historical planning labels in this document remain design notes until replaced by the implementation vocabulary.

## Event families

| Family | Example event types |
|---|---|
| Observation | `RequestObserved`, `MessageObserved`, `AttachmentObserved`, `StateObserved` |
| Intake | `RequestRegistered`, `ValidityAssessed`, `ClarificationRequested`, `ScopeAmended` |
| Routing | `TransferAssessed`, `TransferNotified`, `TransferReceived` |
| Time | `DeadlineCalculated`, `ExtensionAssessed`, `ExtensionNotified`, `OverdueFlagged` |
| Search | `SearchPlanDrafted`, `SearchPerformed`, `RecordsIdentified`, `NoRecordsFound` |
| Consultation | `ConsultationRequired`, `ConsultationStarted`, `ConsultationResponseObserved` |
| Decision support | `LegalIssueFlagged`, `WithholdingGroundFlagged`, `PublicInterestIssueFlagged`, `DecisionPackDrafted` |
| Certification | `HumanDecisionCertified` |
| Communication | `DecisionCommunicated`, `ReleaseMade`, `RefusalCommunicated`, `ChargeNoticeSent` |
| Publication | `DisclosureLogCandidateCreated`, `PublicationObserved` |
| Review/complaint | `ComplaintObserved`, `ReviewOutcomeObserved` |
| Closure | `Closed` |

## Epistemic statuses

Every event and derived field should carry one of:

| Status | Meaning |
|---|---|
| `observed` | Directly present in a source artefact. |
| `inferred` | Derived from source evidence by deterministic or model-assisted logic. |
| `asserted` | Claimed by a system or agent without independent certification. |
| `certified` | Approved by an authorised human actor. |
| `unknown` | Not known or not safely derivable. |

## Certification boundary

Decision-like events require human certification. Examples:

- granting access;
- refusing access;
- withholding under a statutory ground;
- applying a public-interest balance;
- approving redactions;
- imposing or waiving charges;
- extending time limits where statutory judgement is required;
- transferring all or part of a request;
- determining review/complaint outcomes.

The schema should permit agents to draft or flag these events, but not to mark them final.
