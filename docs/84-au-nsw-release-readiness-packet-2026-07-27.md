# AU-NSW release-readiness packet

## Disposition

`foio-au-nsw` is release-ready only as a bounded, local, empirically evaluated
extractor/profile surface. This packet is preparation evidence; it is not a
release, publication, redistribution, or merge authorization.

## Pinned maturity evidence

| Artifact | SHA-256 |
| --- | --- |
| Maturity decision | `996d26686aa5f8b7e4d92d8c4fcf75cc2d0ad8fef65ca9bde47e5b80cb9b67f8` |
| v3 annotation report | `c783713789b33cdd3eb25e4cd5b374f0c609fb63c6b4728bf0cf933eed54dd82` |
| v3 reliability | `dfa2737ce95a18afd76dd2d286ec3881532a306ad7cdda55b245bf42ea3a4d91` |
| Extractor metrics | `eb80191aecbcd6888d65d03821cb88f5c0e69b2dcf02b356155a9e68c6118374` |
| Codebook | `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6` |

## Validation evidence

- Profile registry validator: `ok: true`, 3 profiles.
- AU-NSW contract/profile suite: `50 passed`.
- Repository examples validation: `examples ok`.
- Release/publication metadata tests: `11 passed`.
- Candidate extractor metrics: label accuracy `13/15`, exact-span accuracy
  `15/15`.
- Registry status: `approved_bounded_extractor_mature` at
  `empirically-evaluated` stage.

## Scope and non-release boundaries

The mature designation applies only to the approved AU-NSW ontology and the
15-unit v3 holdout evidence. It does not support population-wide inference,
legal certification, gold-label promotion, publication, redistribution,
training, or release of source text. The 2-unit label disagreement queue
remains recorded for future calibration.

## Remaining gates

| Gate | Status |
| --- | --- |
| Gold promotion | Not authorized; remains blocked |
| Population-wide inference | Prohibited |
| Publication/redistribution/training | Not authorized |
| Push, pull request, merge | Not authorized |
| External release or registry submission | Not performed |

No external action was taken in preparing this packet.

Remaining approval routing is recorded in
`docs/85-au-nsw-remaining-gates-approval-packet-2026-07-27.md`.
