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

## Candidate NZ evidence registers

`mappings/nz-source-rights-registry.yaml` records hash-pinned provider terms
retrieved on 2026-07-16. It distinguishes legislation content, Ombudsman
content, covered Govt.nz material, and third-party FYI request content. The
registry is candidate-only: legislation and covered Govt.nz terms provide
positive reuse evidence, Ombudsman material requires contact for non-personal
reuse, and FYI's publication/takedown policy does not provide a downstream
licence for correspondence or attachments.

`mappings/nz-oia-version-index.yaml` records the 50 official versions listed by
New Zealand Legislation from enactment through 5 April 2025. Each official PDF
was downloaded to temporary local storage, verified as PDF content, and
SHA-256-pinned using `scripts/pin_oia_version_hashes.py`; the PDFs themselves
are not committed. The index does not assign event-time applicability
intervals. Those intervals, the provider-scope interpretation, and source-pack
promotion still require named human review.
