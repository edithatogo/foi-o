# FOI-O NZ terminology crosswalk

This crosswalk keeps source terminology, FOI-O NZ vocabulary, validation
surfaces, and certification language aligned.

| Term family | Source terms or paths | FOI-O NZ representation | Boundary |
| --- | --- | --- | --- |
| Source states | FYI/Alaveteli labels such as `successful`, `waiting_response`, `requires_admin` | Preserved as `source_state`; mapped to normalised state with method, confidence, and evidence. | Source label is not a legal conclusion. |
| Request states | `vocab/request-states.skos.ttl`, `schemas/json/request-profile.schema.json` | Controlled vocabulary plus request-profile fields. | NZ profile only. |
| Event types | `vocab/event-types.skos.ttl`, `schemas/json/core-event.schema.json` | Observed or candidate process events. | Decision-like event finality requires human certification. |
| Assertion status | `vocab/assertion-status.skos.ttl` | `observed`, `inferred`, `asserted`, `certified`, `unknown`. | Automated output should not become certified without authorised evidence. |
| Agent boundaries | `vocab/agent-boundaries.skos.ttl`, `docs/04-agent-boundaries.md` | Safe, review-required, and prohibited autonomous actions. | Agents can assist; humans certify. |
| Legal sources | `mappings/nz-legislation-sources.yaml`, `docs/06-legal-versioning.md` | Source ids, provider candidates, version ids, retrieval times, applicability basis. | Live legal-source freshness is external. |
| Reporting metrics | `mappings/psc-oia-statistics-profile.yaml`, `docs/21-psc-reporting-profile.md` | Derivability classes and public-data caveats. | Not official PSC reporting. |
| Validation surfaces | `schemas/json/`, `shacl/`, `tests/`, `scripts/validate_examples.py` | JSON Schema, SHACL, tests, examples, and CLI validation. | Passing local checks does not complete external gates. |
| Publication assets | `docs/25-generated-asset-index.md`, `examples/generated-asset-manifest.foi-o-publication.json` | Captions, alt text, source inputs, commands, provenance, intended location. | Publication upload and acceptance remain human/external gates. |

## Preferred Phrasing

- Use "candidate event" for extracted or inferred process events.
- Use "human-certified outcome" for final decision-like outcomes.
- Use "repo-local proof" for deterministic tests, examples, and schemas.
- Use "external gate" for live systems, credentials, human approvals, or
  publication platforms.
- Use "FOI-O NZ" for the implemented profile.
- Use "FOI-O" for the reusable design method only when the text also states that
  non-NZ validation remains future work.
