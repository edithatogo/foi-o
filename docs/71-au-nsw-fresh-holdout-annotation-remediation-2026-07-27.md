# AU-NSW fresh holdout annotation remediation

## Defect disposition

The first fresh-holdout runner incorrectly used one shared regex for both
annotator roles. Its report SHA-256 `83dfd246d5e51fcb6a05decfb5fd72ac66ca77ede2a16fb59146bcab5c660683`
and derived reliability SHA-256 `3a63a044e7b54c73ef76d6dd877b9dd06965d215cb7e130d0d20323341889ca3`
are retained as invalid negative evidence and must not be used for review,
promotion, or inference.

## Corrected run

The runner now applies the existing role-specific observed patterns to the two
independent annotators. A new restricted-local run was written to
`/Volumes/PortableSSD/foio-restricted/au-rtk-30236042144/au-nsw-remediation-annotation-v2/`.

- Membership: `2acdb55b8679a060175eaca7c2183e90e59a557fb53fc992df45c965275f8d91`
- Codebook: `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6`
- Report SHA-256: `13512e12edd236e5097548024b9332751c736bbcec9117beeda10ba0af642871`
- Units: 15
- Disagreements: 10
- Adjudications: 10

The corrected run is annotation/adjudication evidence only. Reliability must
be recomputed from this new locked report under a fresh explicit approval.
