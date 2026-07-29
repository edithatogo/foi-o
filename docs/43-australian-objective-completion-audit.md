# Australian pilot objective completion audit

Audit date: 2026-07-29. This is an evidence index, not a legal certification,
publication, or population-wide inference decision.

| Objective item | Current evidence | Status | Remaining boundary |
| --- | --- | --- | --- |
| Commonwealth legislation adapter and source evidence | `examples/v2/australian-legislation-adapter-integration-2026-07-23.approved.json`; `examples/v2/australian-source-pack-au-cth-2026-07-26.approved.json`; source-pack SHA-256 `19dc7ddf07f3bcff38c13f4073f373e5545a316e8e5b922808b41415683e50d4` | Bounded integration and source-pack maturity approved | No publication, redistribution, training, legal certification, unbounded inference, or broader promotion |
| NSW GIPA adapter and source pack | `examples/v2/australian-source-pack-au-nsw-2026-07-23.approved.json`; source artifact `2eb550bd…3891e9` | Bounded adapter/source-pack evidence approved | Platform-capture and legal-review dimensions remain blocked |
| fyi-cli capture support | `examples/v2/australian-fyi-cli-capability-audit-2026-07-23.json` | Generic bounded Alaveteli capture verified for AU-CTH/AU-NSW | RightToKnow source access, not CLI capability |
| Read-only capture and archive infrastructure | `fyi-archive` commits `91eef8b`, `44e2587`, `b2eb327`, `e84b559`, `292a757`, `8d09d57`, `4d410d6`, `fc52b52`; [recovery plan](../conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.md) | Registry-driven, paginated, hash-recording IA acquisition and bounded replay are implemented; complete CDX and replay artifacts are retained under restricted scope | No unbounded archive expansion or publication follows from the bounded artifacts |
| AU-CTH bounded empirical work | `examples/v2/au-cth-fulltext-sample-freeze.approved.json`, `au-cth-assertion-codebook.v0.2.0.approval.json`, `au-cth-annotation-execution.approved.json` | Completed within approved bounded scope | No generalisation, release, or gold promotion |
| AU-CTH reliability and extractor maturity | `examples/v2/au-cth-maturity-decision.approved.json` | Mature only for approved ontology and bounded evidence scope | No legal certification or population-wide inference |
| NSW empirical frame, codebook, packets, metrics, maturity | `docs/84-au-nsw-release-readiness-packet-2026-07-27.md`; `examples/v2/au-nsw-maturity-decision.approved.json` | Bounded local frame, paired/fresh holdout, annotation, reliability, extractor metrics, and maturity evidence complete | No gold promotion, population inference, publication, redistribution, training, legal certification, or external release |
| PR #88 merge | Historical audit records merge commit `1796e88909d029f716774ef201e2f12d0ee68c3a` | Recorded complete | No action required unless repository state contradicts this record |

## Ontology-pinned NLP handoff

The production Australian placeholder was replaced by the metadata-only,
ontology-pinned AU-CTH extraction bundle in `nlp-policy-nz` PR #185, merged at
revision `e4a8cf36090be8c22106072514d9098d27445244`. The handoff preserves
authentic-source hashes and review-bounded output while keeping synthetic
fixtures confined to tests. AU-NSW remains separately scoped to its approved
FOI-O extractor evidence; no unapproved cross-profile bundle is implied.

## NSW fail-closed boundary

The earlier failed CDX attempts remain negative evidence and are not source
populations. A later complete CDX artifact and bounded replay were separately
approved and validated. The complete CDX artifact contains 26,000 metadata
records and is pinned by CDX SHA-256
`954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`.
The bounded replay selected 2,082 canonical captures; classification produced
179 AU-NSW records. The restricted-local immutable manifest, 115-unit NSW
frame, 100-unit paired membership, 15-unit fresh holdout, v3 reliability, and
extractor metrics are all recorded in the numbered AU-NSW evidence packets.

These artifacts do not turn the RightToKnow population into a public dataset,
do not authorize live-origin access, and do not remove the platform-capture,
legal-review, publication, or external-release gates.

### Historical negative evidence

The direct RightToKnow discovery endpoint returned HTTP 403. The exact NSW
Health and NSW Treasury CDX feed queries and broader RightToKnow request-page
probe returned empty arrays. The authorized all-captures run `30068038481`
then failed after bounded retries with an Internet Archive CDX connection
refusal. It retained a 90-day failure artifact only (ZIP SHA-256
`5efe286d76f2ce7bcd71c866e4f6504dcecdd517fed9d951277792777f233237`), not
a retrieval artifact. Empty, capped, or failed Internet Archive results cannot
become source populations, immutable empirical manifests, annotation inputs,
or maturity evidence.

The next permissible NSW empirical action is to validate a non-empty,
rights-cleared artifact with `scripts/validate_australian_source_artifact.py`,
then seek approval of its exact hash, coverage, exclusions, and use scope.
