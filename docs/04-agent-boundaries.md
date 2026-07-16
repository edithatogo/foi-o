# Agent boundaries

FOI-O is a global process model that began with the New Zealand OIA reference
profile and has been iterated through Australian Commonwealth and NSW adapter
work. Its agents are bounded twice: by the universal human-certification
boundary and by an explicit versioned jurisdiction profile. The agent-facing
layer should make authority escalation and cross-jurisdiction legal leakage
structurally difficult.

## Jurisdiction workflow

Before any state mapping, event interpretation, clock calculation, legal-issue
flag, reporting transform, or correspondence draft, an agent must:

1. receive an explicit jurisdiction, regime, profile identifier, and profile
   version;
2. validate the profile's core compatibility, promotion state, source pins,
   and declared capability;
3. apply only the mappings, sources, clocks, review pathways, and vocabulary in
   that profile;
4. fail closed when the profile is missing or incompatible; and
5. keep output candidate-only when the profile or capability is not promoted.

NZ remains the originating and currently implemented package profile.
Australian Commonwealth and NSW are later jurisdiction iterations and remain
candidate adapters until their empirical and human-promotion gates pass. An
agent must not infer that an NZ concept applies in Australia or that a concept
from one Australian jurisdiction applies in another.

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
- requested follow-on actions, when an agent proposes one;
- audit trace.

## Guardrail replay checks

Guardrail replay should be run before using agent outputs in downstream
automation:

```bash
uv run foi-o-nz replay-guardrails \
  --actions-jsonl data/processed/agent-actions.jsonl \
  --events-jsonl data/processed/events.jsonl \
  --output data/processed/guardrail-replay.json
```

The replay report blocks any `requested_follow_on_actions` that match the
action policy's `prohibited_follow_on_actions`. Preparatory actions that pass
policy checks still emit provenance-preserving informational findings when
`audit_trace` is present, and warnings when provenance is missing. A passing
replay report is guardrail evidence only; it does not certify legal correctness,
release/refusal outcomes, redactions, charges, transfers, extensions, or
complaint/review outcomes.

## Tooling implication

Future MCP tools should be narrow, explicit, and non-dispositive. For example:

Good:

```text
calculate_indicative_deadline(request_received_at, jurisdiction, regime)
extract_candidate_events(source_record)
validate_event_log(event_log)
draft_search_plan(request_text, authority_context, jurisdiction_profile)
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

## Global does not mean jurisdiction-agnostic law

“Global” describes the reusable FOI-O core, evidence model, provenance,
epistemic statuses, workflow primitives, and governance boundary. It does not
mean that legal rules are universal. Every jurisdiction profile is independently
versioned and independently promoted; agents may compare profiles only when the
source, temporal, sampling, and semantic comparability evidence permits it.
