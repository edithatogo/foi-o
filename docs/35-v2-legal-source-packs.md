# Legal-policy and jurisdiction source packs

Jurisdiction profiles consume versioned source packs covering current and
historical legislation, regulations, commencement and gazette instruments,
parliamentary material, review findings, guidance, working-day calendars,
authority identity histories, and rights records.

Each normative source has legal effective time and observation/retrieval time.
Profiles resolve law at event time. Later materials may be linked as
retrospective context but cannot silently determine historical legal status.
`nlp-policy-nz` can propose concepts and source spans; review status and
extraction provenance remain mandatory.

Authority identity is also temporal. The `authority-identity-record` contract
preserves official and platform names, platform identifiers, active periods,
predecessor/successor or merger relationships, source evidence, unresolved
identity conflicts, and review status. Approved identity records require a
content hash. This prevents renamed, split, merged, or abolished bodies from
being treated as one timeless entity.

A source pack groups identifiers and manifests; it does not embed or silently
redistribute every underlying source. Rights review is required before any raw
or derived legal-policy content is released.
