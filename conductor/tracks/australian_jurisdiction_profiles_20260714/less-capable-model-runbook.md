# Deterministic Australian profile runbook

## Operating contract

Use profile identifiers `foi-o-au` and `foi-o-au-<subdivision>` with ISO
jurisdictions `AU` and `AU-NSW`, `AU-VIC`, and so on. Do not create long-lived
Git branches for jurisdictions. Do not infer equivalence between NZ,
Commonwealth, state, or territory concepts.

Execute one packet at a time. On a missing source, rights uncertainty, schema
failure, or legal ambiguity, record the exact blocker and stop. Automated agents
cannot approve source rights, legal mappings, gold fixtures, or profile maturity.

## AU-00: preflight

```bash
git status --short --branch
uv run pytest -q tests/test_empirical_schema_fixtures.py
```

Read, in order:

1. `docs/39-ontology-versioning-and-jurisdiction-profiles.md`
2. `schemas/json/ontology-release-manifest.schema.json`
3. `schemas/json/jurisdiction-source-pack.schema.json`
4. this track's `spec.md`
5. this track's `plan.md`

## AU-01: neutral interface

- Create failing tests for profile identity, parent compatibility, bitemporal
  sources, unknown versions, and cross-profile isolation.
- Add the country profile `foi-o-au`; do not add substantive state mappings yet.
- Pin the `edithatogo/legislation` source-pack digest.
- Verify focused tests and record exact results.

## AU-02: Commonwealth pilot

- Create candidate vocabulary, process, clock, review, source, and calendar
  mappings from pinned primary sources.
- Separate observed facts, deterministic calculations, interpretations, and
  human-only determinations.
- Add positive, negative, historical, and non-equivalence examples.
- Stop before stable/gold promotion.

## AU-03: NSW pilot

- Profile ID: `foi-o-au-nsw`; jurisdiction: `AU-NSW`.
- Parent: `foi-o-au` with an explicit compatible version range.
- Model GIPA proactive, informal, and formal pathways as distinct candidates.
- Add negative tests rejecting Commonwealth or NZ rules when no explicit
  comparative mapping exists.
- Stop before stable/gold promotion.

## AU-04: empirical gate

- Freeze sample IDs and digests before extraction.
- Store raw `fyi-archive` provenance separately from derived Hugging Face
  coordinates and digests.
- Require dual annotation and adjudication for maturity claims.
- `nlp-policy-nz` outputs remain candidates regardless of model confidence.

## AU-05: expansion

Only begin after a recorded human go/no-go decision for Commonwealth and NSW.
Execute ACT/Queensland, Victoria/Western Australia, and South
Australia/Tasmania/Northern Territory as separate packets. A failure in one
profile must not block or silently alter another profile.

## Completion record

After each packet, add command, exit code, result count, output paths, source
revisions/digests, commit SHA, and unresolved human gates to `plan.md`.
