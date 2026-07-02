# PSC reporting profile

FOI-O NZ maps public FYI-derived event logs to PSC-style reporting categories for research and reconciliation. These outputs are not official PSC reporting and must not be used as agency performance returns.

## Commands

```bash
uv run foi-o-nz reporting-metrics
uv run foi-o-nz psc-report examples/events.psc-report-sample.jsonl --output examples/psc-report.small.json
```

`reporting-metrics` emits schema-validated metric descriptors from `mappings/psc-oia-statistics-profile.yaml`. `psc-report` reads event JSONL and writes a deterministic aggregate report validated by `schemas/json/psc-report.schema.json`.

## Derivability Classes

| Derivability | Meaning | Example |
| --- | --- | --- |
| `public_fyi_derivable` | Can be counted directly from the supplied public event stream. | `fyi.public_platform_requests` |
| `partially_derivable` | Public events can provide an indicator, but official reporting needs agency records or richer evidence. | `psc.completed_requests`, `psc.extensions`, `psc.refusals` |
| `agency_internal_required` | Public observations are context only; official metric values require agency or Ombudsman records. | `psc.ombudsman_complaints` |
| `not_derivable` | Public FYI data cannot support the metric. | `psc.processing_costs` |

## Sample Output Expectations

The committed sample report at `examples/psc-report.small.json` is regenerated from `examples/events.psc-report-sample.jsonl`.

- Public FYI indicators can have integer `value` fields.
- Partial count-style metrics can have integer `value` fields only when the value is the public event indicator itself.
- Timeliness and average response-time metrics keep `value: null` because the official calculation needs reliable receipt/decision timestamps, extension records, and authoritative working-day treatment.
- Agency-internal-required and not-derivable metrics keep `value: null` and provide warning fields.
- Every metric carries `official_reporting_caveat` and public-data limitation fields.

## Boundary

The profile is designed to make public-data limits visible. It does not certify OIA compliance, replace agency PSC returns, infer demographic/requester categories, or estimate staff time or cost from public correspondence.
