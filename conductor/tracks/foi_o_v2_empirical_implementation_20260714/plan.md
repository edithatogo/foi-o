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
    fields are null. Read-only upstream inspection pins `fyi-archive` revision
    `7e405aa` and `nlp-policy-nz` revision `4150ac3`; the latter has an adapter
    and two-record evaluation, but remains synthetic and placeholder-pinned,
    lacks a raw-manifest entry point and real model pin, and declares contract
    `2.0.0` rather than this repository's candidate contract `0.1.0`. See
    `reextraction-readiness.md`.
  - [x] Readiness subtask: add a read-only, hash-verifying input audit and run it
    against the verified 33,217-record manifest without committing raw records
    (`a15f4d5`). Output: `examples/v2/reextraction-input-audit.fc27.json`;
    33,217 valid content digests, no duplicate/missing request IDs, zero declared
    licences, `ready_for_reextraction: false`. Verification: 14 focused tests;
    82.79% module coverage; full suite 303 passed, 2 skipped.
  - [x] Upstream readiness subtask: pin current archive/NLP revisions and
    implementation evidence in a strict fail-closed audit (`ad65e7f`). Output:
    `examples/v2/upstream-extraction-readiness.2026-07-16.json`. It separates
    the archive's verified 33,217-record publication from extraction readiness
    and records the synthetic fixture, placeholder source pins, missing raw
    entry point/model pin, pending independent annotation, and contract-version
    mismatch. Verification: 16 focused tests; example validation and targeted
    Ruff passed; full suite 328 passed, 2 skipped.
- [x] `[HUMAN]` Pin and approve the target revision for upstream review.
  - Scope of approval (2026-07-16): repeated human direction to continue permits
    repo-local preparation against verified Hugging Face commit
    `fc27bfa471c598a31d975cfa2b603b1a11408e55` only. It does not approve a
    rights rule, heldout selection, label/gold promotion, upstream PR, dataset,
    release, or publication. The real baseline artifact and immutable
    `nlp-policy-nz` pipeline/model revision remain missing.
- [x] `[HUMAN]` Approve stable labels, gold fixtures, and official legal mappings.
  - `APPROVED 2026-07-16`: named reviewer `edithatogo` explicitly approved all
    four hash-pinned review items. The approval is recorded at
    `2026-07-16T09:34:52Z` in
    `examples/v2/human-promotion-review-packet.approved.json` (`99fe183`).
  - [x] Review-packet subtask: SHA-256-pin the independent fixture set, legal
    source mapping, OIA version index, and rights registry in
    `examples/v2/human-promotion-review-packet.approved.json` (`533fae4`, then
    approved in `99fe183`). The
    schema locks reviewer fields and decisions to pending and promotion to
    false, while explicitly excluding schema-valid contract examples as human
    approval evidence. Verification: 13 focused tests; example validation and
    targeted Ruff passed; full suite 331 passed, 2 skipped.
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
- [x] Build deterministic source-triangulation assertions and an explicit human
  exception queue for blocked, conflicting, stale, rights-uncertain, or
  insufficient evidence (`2ce322b`).
  - Output: strict Pydantic input/result records and deterministic evaluator in
    `src/foi_o_nz/source_triangulation.py`, machine-readable result schema, and
    a candidate fail-closed example.
  - Behavior: two distinct eligible supporting sources are required; exception
    reasons and identifiers are stably sorted; human review is always required
    and promotion is always disabled.
  - Verification: focused empirical suite (exit 0; 83 passed); new module
    coverage 98%; targeted Ruff checks passed; `uv sync --extra dev --extra rdf`
    (exit 0); `uv run pytest -q` (exit 0; 314 passed, 2 skipped).
- [ ] Populate and review NZ historical source packs and the source-rights registry.
  - `BLOCKED 2026-07-16`: authoritative rights evidence and the complete
    50-version OIA PDF sequence are now hash-pinned, but event-time applicability
    intervals, non-legislation historical sources, provider-scope interpretation,
    and source-pack promotion still require a named human reviewer. The older
    schema-valid examples remain contract fixtures, not evidence.
  - [x] Evidence subtask: populate a candidate, hash-pinned source-rights
    registry and OIA historical version index from official provider evidence
    while retaining human approval (`127bbf5`).
    Verification: four provider pages and all 50 official OIA PDFs fetched to
    temporary storage and SHA-256-pinned; focused schema/history suite (exit 0;
    76 passed); pinning helper coverage 100%; targeted Ruff checks passed;
    `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q` (exit 0;
    326 passed, 2 skipped). Source HTML/PDF files were not committed.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
  - `BLOCKED 2026-07-16`: the pinned `fc27bfa` manifest has 33,208 empty state
    values, nine unmapped `dry-run` values, no records in a mapped FYI state,
    no correspondence fields, and no non-empty attachment arrays. A substantive
    mapping audit requires a rights-cleared correspondence/attachment-bearing
    source snapshot; this manifest cannot answer the audit question.
  - [x] Readiness subtask: add a read-only, hash-verifying aggregate audit and
    reproduce `examples/v2/raw-state-audit-readiness.fc27.json` from the local
    pinned manifest without committing or modifying source records (`02f75c7`).
    Verification: focused state/normalisation/maturation suite (exit 0; 21
    passed); new module coverage 93%; targeted Ruff checks passed;
    `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q` (exit 0;
    318 passed, 2 skipped).
- [ ] Freeze the empirical sample, dual-annotate, adjudicate, and evaluate reliability.
  - `BLOCKED 2026-07-16`: no authentic frozen unit manifest, duplicate-cluster
    registry, dual-annotation records, adjudication decisions, or agreement
    outputs exist. The schema-valid sample examples use repeated placeholder
    hashes, `zenodo:pending`, and paths to absent Parquet artifacts. Completion
    requires a rights-approved source population, human-approved sampling and
    annotation protocols, at least two independent human annotators, and an
    identified adjudicator. No sample membership, labels, adjudication outcome,
    or reliability statistic may be inferred from the contract fixtures.
- [ ] Generate a versioned release-evidence bundle containing tag/SHA, contract
  versions, capabilities, tests, fixtures, provenance, empirical results,
  exceptions, migrations, and limitations.
  - `BLOCKED 2026-07-16`: there is no eligible immutable release target because
    governed re-extraction, historical source/right review, correspondence-backed
    state mapping, independent fixture promotion, and empirical annotation,
    adjudication, and reliability evaluation remain incomplete. A readiness
    checkpoint must not be presented as the required release-evidence bundle.
- [ ] Trigger the RaC Conformance paper-update workflow only after the release
  bundle is immutable and published.
  - `BLOCKED 2026-07-16`: the prerequisite immutable published release-evidence
    bundle does not exist. An external arXiv record for the earlier methods
    manuscript now exists as `arXiv:2607.02947`; this task did not create or
    modify it, and it does not satisfy the V2 release-bundle prerequisite. No
    RaC paper-update workflow has been triggered.
- [x] `[HUMAN]` Authorize creation of the GitHub issues required to coordinate
  recommended repository changes.
- [ ] `[HUMAN]` Authorize any PR, dataset, release, or preprint action.
