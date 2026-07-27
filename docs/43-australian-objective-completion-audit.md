# Australian pilot objective completion audit

Audit date: 2026-07-25. This is an evidence index, not a legal certification,
publication, or population-wide inference decision.

| Objective item | Current evidence | Status | Remaining boundary |
| --- | --- | --- | --- |
| Commonwealth legislation adapter and source evidence | `examples/v2/australian-legislation-adapter-integration-2026-07-23.approved.json`; `examples/v2/australian-source-pack-au-cth-2026-07-26.approved.json`; source pack `19dc7ddf…e50d4` | Bounded integration and source-pack maturity approved | No publication, redistribution, training, legal certification, unbounded inference, or broader profile promotion |
| NSW GIPA adapter and source pack | `examples/v2/australian-source-pack-au-nsw-2026-07-23.approved.json`; source artifact `2eb550bd…3891e9` | Source-ready, adapter-validation scope only | NSW request population remains unavailable |
| fyi-cli capture support | `examples/v2/australian-fyi-cli-capability-audit-2026-07-23.json` | Generic bounded Alaveteli capture verified for AU-CTH/AU-NSW | RightToKnow source access, not CLI capability |
| Read-only capture and archive infrastructure | `fyi-archive` commits `91eef8b`, `44e2587`, `b2eb327`, `e84b559`, `292a757`, `8d09d57`, `4d410d6`, `fc52b52`; [recovery plan](../conductor/tracks/australian_jurisdiction_profiles_20260714/nsw-source-recovery-20260724.md) | Registry-driven, paginated, hash-recording IA acquisition implemented; scheduled URL indexes and manual all-captures exports are distinct; runs `30068038481`, `30075664496`, and `30176570901` retained failure evidence without partial exports | A new, separately authorized capture or separately approved operator-supplied candidate must satisfy validation before rights review or empirical use |
| AU-CTH bounded empirical work | `examples/v2/au-cth-fulltext-sample-freeze.approved.json`, `au-cth-assertion-codebook.v0.2.0.approval.json`, `au-cth-annotation-execution.approved.json` | Completed within approved bounded scope | No generalisation, release, or gold promotion |
| AU-CTH reliability and extractor maturity | `examples/v2/au-cth-maturity-decision.approved.json` | Mature only for approved ontology and bounded evidence scope | No legal certification or population-wide inference |
| NSW empirical frame, codebook, packets, metrics, maturity | [AU-NSW profile registry maturity update](83-au-nsw-profile-registry-maturity-update-2026-07-27.md); decision artifact `examples/v2/au-nsw-maturity-decision.approved.json` | Registry recognizes bounded extractor maturity | No gold promotion, population inference, publication, or release |
| PR #88 merge | Historical audit records merge commit `1796e88909d029f716774ef201e2f12d0ee68c3a` | Recorded complete | No action required unless repository state contradicts this record |

## Current machine-readable blocker reduction

`phase-3-readiness.json` now evaluates each profile independently. AU-CTH's
approved archive, sampling configuration, automated annotation roles,
adjudication, reliability metrics, and bounded maturity decision no longer
appear as missing merely because AU-NSW is blocked. The production Australian
placeholder in `nlp-policy-nz` is replaced by a metadata-only, ontology-pinned
bundle was integrated into the NLP repository's default branch by PR #185 at
merged revision `e4a8cf36090be8c22106072514d9098d27445244`.

The remaining programme blockers are NSW-specific rights/accessibility review
and the later empirical gates. A non-empty, hash-pinned 179-record AU-NSW
candidate now exists within the approved RightToKnow replay population, but it
is restricted-local and has not received the separate rights/accessibility and
frame-creation approvals required for empirical use. No NSW codebook, frame,
annotation packet, metric, or maturity artifact may be manufactured ahead of
those gates.

## NSW fail-closed boundary

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

## AU-CTH second authorized all-captures attempt

The separately authorized AU-CTH RightToKnow all-captures run `30075664496`
used `au-rtk`, `www.righttoknow.org.au/request/*`, page size `1000`, maximum
pages `1000`, and runtime `600` seconds. It failed safely after bounded Internet
Archive CDX retries with connection refusal. The retained 90-day failure ZIP is
artifact `8589791549`, 530 bytes, SHA-256
`5726f087090ee2c8abef46ab7c425c4c491bd5e0673b0cd8e640f97778728c72`.
It contains failure evidence only—not a CDX export, source population, or
rights/provenance assessment. No importer, enrichment, manifest, empirical
freeze, annotation, or promotion is permitted from this result.

## AU-CTH third authorized all-captures attempt

The separately authorized AU-CTH RightToKnow all-captures run `30176570901`
used `au-rtk`, `www.righttoknow.org.au/request/*`, page size `1000`, maximum
pages `1000`, and runtime `600` seconds. It ran on `fyi-archive` commit
`ab1080c20cdfa9c342d96b18ba2e93f3d28c7945` and failed safely after bounded
Internet Archive CDX retries when the TLS handshake timed out. The retained
90-day failure ZIP is artifact `8624447034`, 535 bytes, SHA-256
`954af9aa0b844484cc9d88cf3a6b5bb9812644176b237c238f0419ec82fe1449`.
Its only member is `retrieval.json`, SHA-256
`e9a6735eb3fbf803e07c04fcbb1ff2446cd819cd1f65effb0900e98c7a77554d`, which
records `retrieval_status=failed`, `pagination_complete=false`, and no response
hash or record count. This is negative failure evidence only—not a CDX export,
source population, rights/provenance assessment, or candidate source artifact.
The authorization is consumed: no fourth retry, replay, import, enrichment,
manifest, empirical freeze, annotation, or promotion follows from this result.
