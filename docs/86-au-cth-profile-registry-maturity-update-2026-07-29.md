# AU-CTH profile registry maturity update

The profile registries now recognize `foio-au-cth` as
`approved_bounded_extractor_mature` at stage `empirically-evaluated`.

The registry pins the approved Commonwealth source-pack candidate
`examples/v2/australian-source-pack-au-cth-2026-07-26.candidate.json` at
SHA-256 `19dc7ddf07f3bcff38c13f4073f373e5545a316e8e5b922808b41415683e50d4`,
the ontology `foio-au-pilot-assertion-v0.2.0`, the 100-unit frozen frame, and
the approved extractor output and metrics hashes recorded in the maturity
decision. This is bounded evidence only: annotation gold, legal promotion,
population-wide inference, publication, redistribution, training, and release
remain prohibited.

Validation is performed by `scripts/validate_jurisdiction_profiles.py` and the
focused profile/source-pack test suite.
