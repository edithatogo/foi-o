# Australian pilot objective completion audit

Audit date: 2026-07-23. This is an evidence index, not a legal certification,
publication, or population-wide inference decision.

| Objective item | Current evidence | Status | Remaining boundary |
| --- | --- | --- | --- |
| Commonwealth legislation adapter and source evidence | `examples/v2/australian-legislation-adapter-integration-2026-07-23.approved.json`; adapter commit `feb55b2` | Bounded integration evidence approved | No general legal promotion implied |
| NSW GIPA adapter and source pack | `examples/v2/australian-source-pack-au-nsw-2026-07-23.approved.json`; source artifact `2eb550bd…3891e9` | Source-ready, adapter-validation scope only | NSW request population remains unavailable |
| fyi-cli capture support | `examples/v2/australian-fyi-cli-capability-audit-2026-07-23.json` | Generic bounded Alaveteli capture verified for AU-CTH/AU-NSW | RightToKnow source access, not CLI capability |
| Read-only capture and archive infrastructure | `fyi-archive` commits `91eef8b`, `44e2587`, `b2eb327`, `e84b559`, `292a757`, `8d09d57` | Registry-driven, paginated, hash-recording IA acquisition implemented; failed runs retain non-partial evidence records | Dispatch remains read-only; rights gate precedes empirical use |
| AU-CTH bounded empirical work | `examples/v2/au-cth-fulltext-sample-freeze.approved.json`, `au-cth-assertion-codebook.v0.2.0.approval.json`, `au-cth-annotation-execution.approved.json` | Completed within approved bounded scope | No generalisation, release, or gold promotion |
| AU-CTH reliability and extractor maturity | `examples/v2/au-cth-maturity-decision.approved.json` | Mature only for approved ontology and bounded evidence scope | No legal certification or population-wide inference |
| NSW empirical frame, codebook, packets, metrics, maturity | `examples/v2/australian-nsw-rtk-capture-plan-2026-07-23.approved.json`; `australian-nsw-rtk-cdx-probe-2026-07-23.blocked.json` | Not achieved | Non-empty, rights-cleared NSW request artifact and exact freeze approval |
| PR #88 merge | Historical audit records merge commit `1796e88909d029f716774ef201e2f12d0ee68c3a` | Recorded complete | No action required unless repository state contradicts this record |

## NSW fail-closed boundary

The direct RightToKnow discovery endpoint returned HTTP 403. The exact NSW
Health and NSW Treasury CDX feed queries and broader RightToKnow request-page
probe returned empty arrays. The later bounded CDX retry did not create a
retrieval artifact. Failed future runs now retain a machine-readable failure
record without any partial export. Empty, capped, or failed Internet Archive
results cannot become source populations, immutable empirical manifests,
annotation inputs, or maturity evidence.

The next permissible NSW empirical action is to validate a non-empty,
rights-cleared artifact with `scripts/validate_australian_source_artifact.py`,
then seek approval of its exact hash, coverage, exclusions, and use scope.
