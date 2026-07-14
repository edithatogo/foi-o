# Deterministic execution runbook

## Operating contract

Execute exactly one packet at a time in identifier order. Do not infer legal
meaning, rename identifiers, promote candidates, publish data, push branches,
or mark a human gate complete. If an input is absent or a command fails, add a
dated `BLOCKED` note to `plan.md` with the exact path/command/error and stop.

Before every packet run:

```bash
git status --short --branch
uv run pytest -q tests/test_empirical_schema_fixtures.py tests/test_empirical_contracts.py
```

Expected baseline: a clean or explicitly documented working tree and passing
focused tests. Preserve unrelated changes.

## V2-01: ontology family manifest

- Inputs: `docs/39-ontology-versioning-and-jurisdiction-profiles.md`,
  `schemas/json/ontology-release-manifest.schema.json`.
- Verify: `uv run pytest -q tests/test_empirical_schema_fixtures.py`.
- Expected: 54 passing tests or more; zero failures.
- Output: validated core/profile version contract. Do not split the Python
  package in this packet.

## V2-02: extraction contract export

- Create: `contracts/foi-o-extraction-contract/0.1.0/manifest.json`.
- Pin: ontology release manifest, schema IDs, codebook version, candidate status
  vocabulary, capability IDs, and migration catalogue.
- Add: one valid and three invalid fixtures under `examples/v2/` using the
  existing fixture naming convention.
- Add or update Pydantic reference records only in
  `src/foi_o_nz/empirical_contracts.py`.
- Verify: focused empirical schema/model tests, then `uv run pytest -q`.
- Stop if any referenced ontology/schema/codebook version is mutable or absent.

## V2-03: compatibility negotiation

- Create failing tests first in `tests/test_extraction_contract.py`.
- Implement exact-version and declared-range acceptance, unknown-major
  rejection, capability discovery, and explicit migration lookup.
- No fallback may silently accept an unknown revision.
- Verify: `uv run pytest -q tests/test_extraction_contract.py`.

## V2-04: consumer contract matrix

- Add fixtures for FOI-O, `fyi-archive`, `nlp-policy-nz`, and one read-only MCP
  consumer under `examples/v2/consumer-contracts/`.
- Record each consumer's accepted and rejected contract versions.
- Verify offline; do not depend on sibling checkout paths.
- Output: `docs/compatibility/foi-o-v2-consumers.json` plus tests.

## V2-05: evidence and publication handoff

- Pin immutable raw `fyi-archive` provenance separately from the derived Hugging
  Face dataset repository, revision, configuration, split, and digest.
- Record `nlp-policy-nz` pipeline/model version for derived candidates.
- Never overwrite raw archive records and never use `main` or `latest` as an
  evidence revision.
- Generate candidate outputs only. Gold/stable/legal promotion is `[HUMAN]`.

## Completion record

For each packet, append to `plan.md`: command, exit code, passing count, output
paths, commit SHA, and remaining human/external gates. Mark only the matching
checkbox complete.
