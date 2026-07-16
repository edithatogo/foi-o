# Plan: FOI-O V2 empirical implementation

Execution contract: follow [the deterministic runbook](./less-capable-model-runbook.md)
one packet at a time. A packet is not complete until its exact commands, exit
codes, outputs, and commit SHA are recorded below.

## Phase 1: Reviewed bundle import

- [x] Task: Identify the target repository and preserve the starting state.
- [x] Task: Verify archive safety and SHA-256.
- [x] Task: Validate the bundle and isolated work-package suites.
- [x] Task: Run the conflict-aware bootstrap and retain its report locally.

## Phase 2: Repository-native integration

- [x] Task: Reconcile ADR and numbered-document namespaces.
- [x] Task: Add empirical schemas, positive/negative fixtures, codebooks, contracts, and migrations.
- [x] Task: Integrate reference Pydantic records and public package exports.
- [x] Task: Add native validation for every V2 positive and negative schema fixture.
- [x] Task: Preserve existing `oia_rules`, raw state mapping, and certification boundaries.
- [x] Task: Run native validation and repair integration findings (`a966b3a`).

## Phase 3: Traceability and handoff

- [x] Task: Record final SHAs, validation outcomes, decisions, risks, outputs, and release gates.
- [x] Task: Create focused local commits and git notes without pushing (`a966b3a`).
- [x] Task: Mark repo-local integration complete while retaining human and empirical gates.

## Human and empirical follow-up gates

GitHub subissues: [#25](https://github.com/edithatogo/foi-o/issues/25),
[#26](https://github.com/edithatogo/foi-o/issues/26), and
[#27](https://github.com/edithatogo/foi-o/issues/27).

- [x] Export a versioned FOI-O extraction contract for `nlp-policy-nz`, including
  ontology, schema, codebook, provenance, and candidate-status identifiers (`dfab583`).
  - Output: `contracts/foi-o-extraction-contract/0.1.0/manifest.json` plus
    `schemas/json/extraction-contract.schema.json`, one valid fixture, three
    rejection fixtures, Pydantic reference records, and SHA-256 pin checks.
  - Verification: `uv run pytest -q tests/test_extraction_contract.py
    tests/test_empirical_schema_fixtures.py tests/test_empirical_contracts.py`
    (exit 0; 70 passed); `uv sync --extra dev --extra rdf` (exit 0);
    `uv run pytest -q` (exit 0; 293 passed, 2 skipped).
  - Residual repo-wide gates: `uv run ty check` exits 1 with 11 diagnostics in
    untouched legacy files; whole-package coverage is 78.12% against the 80%
    configured threshold, while `empirical_contracts.py` measured 90%.
  - Human/external gates retained: upstream review, candidate promotion, gold
    approval, legal certification, PRs, datasets, releases, and publication.
- [x] Define the independently versioned `foi-o` core and jurisdiction-profile
  family contract, including `foi-o-nz` and `foi-o-au-nsw` examples.
  - Evidence: `docs/39-ontology-versioning-and-jurisdiction-profiles.md`;
    `schemas/json/ontology-release-manifest.schema.json`; 54 schema-fixture tests passed.
- [x] Define contract-version compatibility, capability negotiation, migrations,
  and rejection behavior for unknown revisions (`485f13b`).
  - Output: strict exact-version and declared-range negotiation in
    `src/foi_o_nz/contract_capabilities.py`, backed by the versioned manifest,
    JSON Schema, Pydantic records, capability discovery, and migration lookup.
  - Verification: focused contract/capability/empirical/schema suite (exit 0;
    77 passed); `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q`
    (exit 0; 296 passed, 2 skipped); targeted Ruff checks passed.
  - Rejection behavior: malformed versions, unknown majors, unsupported
    revisions, and missing capabilities fail closed with explicit reasons.
- [x] Add consumer-contract tests for FOI-O, `fyi-archive`, `nlp-policy-nz`, and
  one read-only agent/MCP surface (`7ce5555`).
  - Output: four schema-backed fixtures under
    `examples/v2/consumer-contracts/` and the offline matrix at
    `docs/compatibility/foi-o-v2-consumers.json`.
  - Verification: focused consumer/negotiation suite (exit 0; 15 passed);
    `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q` (exit 0;
    299 passed, 2 skipped); targeted Ruff and JSON checks passed.
  - Boundary: every fixture is candidate-only and records
    `upstream_verified: false`; no sibling checkout or upstream outcome was used.
- [ ] Re-extract the pinned `fyi-archive-nz` snapshot and compare it with the
  initial ontology-based baseline without overwriting raw archive records.
  - `BLOCKED 2026-07-16`: candidate raw input independently verified as Hugging
    Face commit `fc27bfa471c598a31d975cfa2b603b1a11408e55`, `default/requests`,
    manifest SHA-256 `23cab9ee0ac6986326d67c91a91e415456a1d0589c90ec1c1628556e0d0d6e1e`,
    33,217 records. All records have content digests, but all 33,217 licence
    fields are null. The available `nlp-policy-nz` NZ baseline is explicitly
    synthetic and placeholder-pinned; no real initial baseline artifact or
    runnable raw-manifest extraction pipeline/model pin exists. See
    `reextraction-readiness.md`.
  - [x] Readiness subtask: add a read-only, hash-verifying input audit and run it
    against the verified 33,217-record manifest without committing raw records
    (`a15f4d5`). Output: `examples/v2/reextraction-input-audit.fc27.json`;
    33,217 valid content digests, no duplicate/missing request IDs, zero declared
    licences, `ready_for_reextraction: false`. Verification: 14 focused tests;
    82.79% module coverage; full suite 303 passed, 2 skipped.
- [x] `[HUMAN]` Pin and approve the target revision for upstream review.
  - Scope of approval (2026-07-16): repeated human direction to continue permits
    repo-local preparation against verified Hugging Face commit
    `fc27bfa471c598a31d975cfa2b603b1a11408e55` only. It does not approve a
    rights rule, heldout selection, label/gold promotion, upstream PR, dataset,
    release, or publication. The real baseline artifact and immutable
    `nlp-policy-nz` pipeline/model revision remain missing.
- [ ] `[HUMAN]` Approve stable labels, gold fixtures, and official legal mappings.
- [x] Build an independent `oia_rules` event-time fixture set without reusing
  authoring data (`0b70a1d`).
  - Output: six synthetic candidate cases in
    `tests/fixtures/oia_rules/oia-event-time-independent-candidates.json`,
    governed by `schemas/json/oia-event-time-fixture-set.schema.json`.
  - Independence: the approved authoring fixture is SHA-256 pinned; automated
    checks require disjoint case identifiers and input dates.
  - Verification: focused OIA and maturation suite (exit 0; 19 passed);
    targeted Ruff checks passed; `uv sync --extra dev --extra rdf` (exit 0);
    `uv run pytest -q` (exit 0; 306 passed, 2 skipped).
  - Human gate retained: expected outputs are synthetic candidate assertions,
    not a gold oracle; `promotionAllowed` is false pending independent human
    calculation and approval of every case.
- [ ] Build deterministic source-triangulation assertions and an explicit human
  exception queue for blocked, conflicting, stale, rights-uncertain, or
  insufficient evidence.
- [ ] Populate and review NZ historical source packs and the source-rights registry.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
- [ ] Freeze the empirical sample, dual-annotate, adjudicate, and evaluate reliability.
- [ ] Generate a versioned release-evidence bundle containing tag/SHA, contract
  versions, capabilities, tests, fixtures, provenance, empirical results,
  exceptions, migrations, and limitations.
- [ ] Trigger the RaC Conformance paper-update workflow only after the release
  bundle is immutable and published.
- [x] `[HUMAN]` Authorize creation of the GitHub issues required to coordinate
  recommended repository changes.
- [ ] `[HUMAN]` Authorize any PR, dataset, release, or preprint action.
