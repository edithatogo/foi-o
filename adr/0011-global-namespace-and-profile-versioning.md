# ADR 0011: global namespace and independently versioned profiles

## Decision

Use `https://w3id.org/foio/` for global semantic artefacts and retain
`foi-o-nz` as a compatibility/profile identity. Profile, capability, source,
archive and paper versions remain independent and are combined only by an
exact lock.

## Consequences

NZ artefacts require explicit migration aliases; no Australian or other
jurisdiction may inherit NZ legal semantics by fallback. Registry submission,
profile promotion and publication remain human-gated.
