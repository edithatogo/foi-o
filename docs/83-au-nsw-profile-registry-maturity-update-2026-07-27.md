# AU-NSW profile registry maturity update

The local profile registry now recognizes `foio-au-nsw` as
`approved_bounded_extractor_mature` at stage `empirically-evaluated`.

The registry pins ontology `foio-au-nsw-pilot-assertion-v0.2.1`, the v3
annotation, reliability, and extractor-metrics hashes, and 15-unit scope.
Population inference and publication are explicitly prohibited. Annotation
gold remains blocked, and legal-review promotion remains blocked.

Validation: `scripts/validate_jurisdiction_profiles.py --root .` returned
`ok: true`; the focused profile tests passed.
