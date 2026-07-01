# Agent boundaries

FOI-O NZ assumes bounded agents. The agent-facing layer should make illegal or unsafe authority escalation structurally difficult.

## Safe agent tasks

Agents may:

- extract public correspondence metadata;
- preserve and normalise source states with confidence;
- calculate indicative statutory clocks;
- identify missing metadata;
- classify request topics;
- draft search plans;
- cluster attachments and candidate records;
- flag possible consultation needs;
- flag possible legal issues for human review;
- draft correspondence templates;
- check decision packs for required fields;
- generate reporting metrics from event logs;
- create disclosure-log metadata candidates.

## Human-certified tasks

Agents must not autonomously certify:

- release or refusal outcomes;
- withholding grounds;
- public-interest balancing;
- redaction approval;
- charges;
- transfers where statutory judgement is required;
- extensions where statutory judgement is required;
- vexatious/frivolous determinations;
- Ombudsman/review outcomes.

## Agent action contract

Every agent action should specify:

- requested capability;
- inputs and evidence references;
- generated outputs;
- assertion status;
- confidence;
- whether human certification is required;
- whether the output has legal effect;
- prohibited follow-on actions;
- audit trace.

## Tooling implication

Future MCP tools should be narrow, explicit, and non-dispositive. For example:

Good:

```text
calculate_indicative_deadline(request_received_at, jurisdiction, regime)
extract_candidate_events(source_record)
validate_event_log(event_log)
draft_search_plan(request_text, authority_context)
```

Risky unless tightly constrained:

```text
determine_withholding_ground(document, request)
approve_redactions(document)
finalise_decision(request)
```

Prohibited as autonomous tools:

```text
refuse_request(request)
release_document(document)
certify_public_interest_balance(request, document)
```
