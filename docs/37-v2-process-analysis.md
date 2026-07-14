# Process analysis

FOI-O owns construction of FOI-specific event logs from existing core events,
ledger records, trace spans, lineage graphs, and evidence assertions. It does
not create a second event system.

Export both case-centric and object-centric views. Process analysis may estimate
public trace variants, observed transitions, censoring-aware latencies, visible
bottlenecks, missingness, and non-derivability. Each analytical execution should
emit a `process-analysis-run` record that pins the input event stream hash,
snapshot, schema, software versions, event-selection rules, uncertainty and
censoring policies, outputs, estimands, and review status.

The run contract hard-codes:

- `legal_claims_permitted: false`;
- `result_scope: public_process_indicators_only`;
- explicit abstention reporting;
- a comparability assessment for cross-jurisdiction analysis; and
- an approver record before an analysis is marked approved.

Process analysis must not invent hidden agency events from silence, equate
public latency with statutory breach, or rank legal compliance without the
required clock facts. Generic mining utilities may later move to a separate
library only after NZ and Australian event logs reveal stable cross-domain
abstractions. FOI-O retains FOI-specific event construction, evidence linkage,
and derivability semantics.

## Rule traces as process evidence

Where an existing deterministic rule contributes a candidate date or process
state, the analysis run records the rule and parameter versions, applicable law
and calendar versions, input epistemic statuses, trace steps, warnings, and
derivability. Rule traces may explain a derived event but do not certify legal
compliance. Independent rule evaluation is specified in
`docs/39-v2-rule-evaluation.md`.
