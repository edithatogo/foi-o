# Remaining Australian jurisdiction dependency register

Recorded 2026-07-31. This is planning evidence, not source-rights approval,
empirical-frame approval, a legal conclusion, or authority to replay archived
content.

## Shared critical path

The seven remaining profiles share the AU RightToKnow Alaveteli platform family
for capture engineering. They do not share legislation, Gazette, effective
dates, rights dispositions, authority mappings, samples, annotation evidence,
or maturity decisions.

The shared implementation sequence is:

1. canonical authority registry and conflict-preserving classifier;
2. reusable provenance, rollout-stage, and core-codebook contracts;
3. legislation provider plus Gazette/equivalent source pack;
4. jurisdiction-specific capture capability and archive manifest;
5. codebook overlay, calibration, annotation, evaluation, and maturity packet.

## Jurisdiction blockers and issue routing

| Profile | FOI-O issue | Legislation issue | Immediate blocker |
| --- | --- | --- | --- |
| AU-SA | [#115](https://github.com/edithatogo/foi-o/issues/115) | [legislation #53](https://github.com/edithatogo/legislation/issues/53) | Verify authoritative formats, machine access, terms, and source fixtures |
| AU-WA | [#116](https://github.com/edithatogo/foi-o/issues/116) | [legislation #56](https://github.com/edithatogo/legislation/issues/56) | Resolve WA/ACT authority ambiguity before source and empirical classification |
| AU-NT | [#117](https://github.com/edithatogo/foi-o/issues/117) | [legislation #50](https://github.com/edithatogo/legislation/issues/50) | Verify terms, formats, and runtime adapter from metadata-only evidence |
| AU-VIC | [#118](https://github.com/edithatogo/foi-o/issues/118) | [legislation #55](https://github.com/edithatogo/legislation/issues/55) | Verify official machine-readable source shape and runtime parser |
| AU-TAS | [#119](https://github.com/edithatogo/foi-o/issues/119) | [legislation #54](https://github.com/edithatogo/legislation/issues/54) | Verify machine-readable source and plan a small-population design |
| AU-ACT | [#120](https://github.com/edithatogo/foi-o/issues/120) | [legislation #111](https://github.com/edithatogo/legislation/issues/111), after source-shape #47 | Implement the runtime provider, preserve authoritative-PDF policy, resolve WA/ACT identities |
| AU-QLD | [#121](https://github.com/edithatogo/foi-o/issues/121) | [legislation #52](https://github.com/edithatogo/legislation/issues/52) | Maintainer API registration, credential custody, terms, rates, and authentic fixtures |

Programme owners remain
[legislation #105](https://github.com/edithatogo/legislation/issues/105),
[fyi-cli #234](https://github.com/edithatogo/fyi-cli/issues/234),
[fyi-archive #210](https://github.com/edithatogo/fyi-archive/issues/210),
[nlp-policy-nz #144](https://github.com/edithatogo/nlp-policy-nz/issues/144)
with config foundation
[#200](https://github.com/edithatogo/nlp-policy-nz/issues/200), and
[foi-process #39](https://github.com/edithatogo/foi-process/issues/39).

Concrete reusable implementation children are
[fyi-cli #283](https://github.com/edithatogo/fyi-cli/issues/283) for the
seven-profile capability audit,
[fyi-archive #317](https://github.com/edithatogo/fyi-archive/issues/317) for
checkpointed content-addressed Wayback replay,
[nlp-policy-nz #200](https://github.com/edithatogo/nlp-policy-nz/issues/200)
for config-driven profiles, and
[foi-process #96](https://github.com/edithatogo/foi-process/issues/96) for the
reusable paired Mermaid/BPMN process template.

## Dependency-first execution policy

External blockers start immediately but do not idle independent work:

- QLD registration/terms and ACT source-track restoration run as early unblock
  lanes.
- Shared authority, provenance, pipeline, and codebook work precedes every
  jurisdiction.
- SA, WA, and NT form the first offline implementation tranche; VIC and TAS
  form the second; ACT and QLD complete when their earlier blockers clear.
- Readiness, not geography, determines which profile advances at any instant.
- Small available populations use a pre-registered census or justified
  small-population design; they are never padded with cross-jurisdiction units.

## Restricted-local metadata indicators

The finalized AU RightToKnow population contains preliminary metadata
indicators for all seven remaining jurisdictions, including records with
conflicting WA/ACT tags. Those indicators are not approved source frames.
Tag-only legal classification is prohibited. Read-only reclassification may
use the finalized manifest metadata after the authority registry is validated;
new full-text replay remains a separate gate.

## Early external blocker

The global legislation/Gazette control track is still held in
[legislation PR #106](https://github.com/edithatogo/legislation/pull/106).
The dependency remediation was pushed. At exact head
`0c0efe877f0b8eb7e5f05a2d89aeec82a09dbf5c`, the pull request is open,
ready, and mergeable; all substantive hosted checks pass and the load-test job
is intentionally skipped. Merge remains a separate human gate.

## Local implementation candidates

The following candidates were implemented in clean temporary clones. Their
commits and Git notes are local only: none has been pushed, opened as a pull
request, merged, activated, or used for source retrieval.

| Repository | Issue/scope | Local candidate | Validation boundary |
| --- | --- | --- | --- |
| fyi-cli | #283 Australian capture capability contracts | `3f3befa8acb07dce492ce41e99457d6da5acfa88` | 740 passed, 2 opt-in network tests skipped; immutable schema/adapter pins and semantic boundaries enforced |
| fyi-archive | #317 checkpointed content-addressed Wayback replay state | `af4c0a47e2d589f295ba2dfebee0f3f7681690f7` | 538 passed, 1 skipped; immutable boundary/approval registries and receipt-bound CDX replacement candidates |
| nlp-policy-nz | #200 config-driven profile foundation | `2a49a516252d6e2c765c4d8a6e53336226e273bf` | 30 focused/regression tests passed; activation registry has zero grants; unrelated repository baselines remain |
| foi-process | #96 paired Mermaid/BPMN jurisdiction template | `8bc0c2c6022a4de08d2e52515af4885ee598a094` | full local CI passed; strict profiles bind to their physical registered repository paths |

An exact-head independent adversarial review accepted all four candidates
within their stated scope. Each still requires an explicit
external-repository push gate before it can enter hosted review.
