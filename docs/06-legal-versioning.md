# Legal versioning

FOI-O NZ should treat law and guidance as time-dependent sources.

## Why it matters

An OIA request from 2019 should not automatically be analysed against 2026 guidance or a future amended Act. Agents need to know what legal source version was used for a calculation or issue flag.

## Minimum legal-reference model

Each statutory or guidance reference should carry:

```yaml
source_id: nz.oia.act
source_title: Official Information Act 1982
provision: s 15
jurisdiction: NZ
provider_candidate: legislation.govt.nz
source_uri: https://www.legislation.govt.nz/...
work_id: act_public_1982_156
version_id: act_public_1982_156_en_YYYY-MM-DD
retrieved_at: 2026-07-01T00:00:00Z
applicability_basis: current_at_event_time | current_at_extraction_time | unknown
```

## Implementation note

The New Zealand Legislation API conceptual model of works, versions, and formats is a good fit for durable statutory references. The project should avoid bare string citations where a provision-level or version-level identifier is available.

`mappings/nz-legislation-sources.yaml` is the repo-local source-version
registry. It records source status, retrieval timestamp, version identifier,
canonical URI, jurisdiction, provider candidate, and applicability basis for
statute and guidance references.

Use `foi-o-nz legal-source-status` for local validation. `--live` does not fetch
network sources; it fails closed unless an ignored cache directory such as
`generated/legal-sources/` exists. This keeps live NZ Legislation/Ombudsman
retrieval as an explicit external gate rather than silently mixing live state
into committed fixtures.
