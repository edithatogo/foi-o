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
  - `BLOCKED 2026-07-16`: the governed one-record local candidate re-extraction
    and deterministic reproducibility delta are complete, but empirical
    comparison remains blocked by absent independent annotation and
    adjudication. The wider 33,217-record Hugging Face manifest remains unusable
    because all licence fields are null and it lacks the content-bearing inputs
    required by the consumer. See `reextraction-readiness.md`.
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
  - [x] Consumer readiness subtask: verify `nlp-policy-nz` revision `ee3fb0b`
    consumes contract `0.1.0`, exposes a raw-manifest extraction entry point,
    and pins Legal-BERT to immutable repository and weights digests. The audit
    remains fail-closed because the available source manifest is not
    content-bearing or rights-cleared, the baseline is synthetic, and
    independent annotation is pending (`60f2671`). Verification: 64 focused
    tests; JSON parsing, targeted Ruff, and diff checks passed; full suite 331
    passed, 2 skipped.
  - [x] Bounded source subtask: record the named-human approval and independently
    verified one-record content snapshot. Pending manifest `d850ca36…` remains
    immutable; approved manifest `c929b312…` is local-only and excludes
    redistribution, publication, training, fine-tuning, release, dataset
    publication, and reviewed/gold-label promotion. This establishes the bounded
    rights/content source only; consumer-adapter, baseline, and independent
    annotation gates remain (`e322da3`). Verification: readiness schema and
    exact-pin tests passed; targeted Ruff passed; `uv sync --extra dev --extra
    rdf` succeeded; full suite 331 passed, 2 skipped. Conductor review bumped
    the readiness contract to `v0.2.0` and removed instance-specific schema
    constants.
  - [x] Initial baseline subtask: generate a real one-record candidate baseline
    with `nlp-policy-nz` revision `7fc78f1`, then independently recompute its
    source, contract, content, candidate, span, and revision evidence with FOI-O
    verifier `baf1b22`. Baseline SHA-256: `90550ce0…`; verification report
    SHA-256: `0702d54e…`. Both remain local-only, candidate status, unpromoted,
    and unpublished. The model pin is recorded but model execution is false
    (`5ff3631`). Verification: 10 focused tests; JSON/YAML parsing and targeted
    Ruff passed; full suite 339 passed, 2 skipped.
  - [x] Governed handoff subtask: return the approved source, archive, fyi-cli,
    NLP pipeline, independent verifier, extraction-contract, initial-baseline,
    and model revisions to FOI-O in the schema-backed packet
    `examples/v2/governed-reextraction-packet.35076.json` (`575f57a`; SHA-256
    `9cc0e849e170c12ba23b292736f40f728fb3bad5dbcf364e26ed279b7a760d82`).
    The packet authorizes local candidate extraction only; redistribution,
    training, fine-tuning, release, dataset publication, publication, and
    reviewed/gold-label promotion remain false. Verification: 11 focused tests;
    JSON/schema checks, targeted Ruff, and Conductor review passed; `uv sync
    --extra dev --extra rdf` succeeded; full suite 346 passed, 2 skipped.
  - [x] Governed execution subtask: run pinned `nlp-policy-nz` revision
    `7fc78f1` against approved request `35076`, independently verify the local
    candidate artifact, and produce a deterministic non-empirical delta
    (`ec5480b`). The candidate SHA-256 is `90550ce0…`, independent verification
    SHA-256 is `23270c27…`, and delta SHA-256 is `7af9bc5e…`; all three are
    read-only under `/private/tmp/foio-governed-reextraction-35076-verified` and
    are not committed. The new artifact is byte-identical to the initial
    baseline: one unchanged candidate, no added/removed/changed/provenance-only
    records. All seven source-artifact hashes were verified and source hashes
    were unchanged before and after execution. Model execution, empirical
    comparison, promotion, publication, and redistribution remain false.
    Verification: targeted type checking; 26 focused tests; JSON/schema checks,
    targeted Ruff, and Conductor review passed; `uv sync --extra dev --extra
    rdf` succeeded; full suite 353 passed, 2 skipped.
- [x] `[HUMAN]` Pin and approve the target revision for upstream review.
  - Scope of approval (2026-07-16): repeated human direction to continue permits
    repo-local preparation against verified Hugging Face commit
    `fc27bfa471c598a31d975cfa2b603b1a11408e55` only. It does not approve a
    rights rule, heldout selection, label/gold promotion, upstream PR, dataset,
    release, or publication. Separately, reviewer `edithatogo` approved the
    immutable one-record manifest `d850ca36…` only for local candidate
    extraction; the verified baseline and governed handoff are now recorded.
    Independent annotation remains missing.
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
  - `BLOCKED 2026-07-16`: authoritative rights evidence, the complete
    50-version OIA PDF sequence, and 50 deterministic candidate event-time
    intervals are hash-pinned. The provider-scope registry is already approved.
    Every candidate interval remains legally unapproved, non-legislation
    historical sources are still absent, and source-pack promotion still
    requires named human review. The older schema-valid examples remain
    contract fixtures, not evidence.
  - [x] Evidence subtask: populate a candidate, hash-pinned source-rights
    registry and OIA historical version index from official provider evidence
    while retaining human approval (`127bbf5`).
    Verification: four provider pages and all 50 official OIA PDFs fetched to
    temporary storage and SHA-256-pinned; focused schema/history suite (exit 0;
    76 passed); pinning helper coverage 100%; targeted Ruff checks passed;
    `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q` (exit 0;
    326 passed, 2 skipped). Source HTML/PDF files were not committed.
  - [x] Interval-candidate subtask: derive 50 explicit inclusive/exclusive
    intervals only from adjacent approved official as-at dates (`c91c02e`).
    Output: `mappings/nz-oia-applicability-interval-candidates.yaml` (SHA-256
    `401cd17a…`). All intervals retain `legal_applicability_approved: false` and
    require named-human commencement/amendment review before source-pack
    promotion. Verification: 12 focused tests; targeted type checking, Ruff,
    JSON/schema checks, and Conductor review passed; full suite 368 passed,
    2 skipped.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
  - `BLOCKED 2026-07-16`: approved request `35076` now supplies one real
    outgoing correspondence item supporting the bounded candidate mapping
    `waiting_response` to `awaiting_response`. Its verified attachment inventory
    is empty, so it cannot satisfy the attachment-bearing audit requirement or
    support an archive-wide claim. Named human mapping review and a separate
    rights-cleared non-empty attachment snapshot remain required.
  - [x] Readiness subtask: add a read-only, hash-verifying aggregate audit and
    reproduce `examples/v2/raw-state-audit-readiness.fc27.json` from the local
    pinned manifest without committing or modifying source records (`02f75c7`).
    Verification: focused state/normalisation/maturation suite (exit 0; 21
    passed); new module coverage 93%; targeted Ruff checks passed;
    `uv sync --extra dev --extra rdf` (exit 0); `uv run pytest -q` (exit 0;
    318 passed, 2 skipped).
  - [x] Bounded correspondence subtask: verify the approved request `35076`
    manifest, raw state, state mapping, one-item correspondence structure, and
    empty attachment inventory without committing source content (`9b50e36`).
    Output: `examples/v2/bounded-raw-state-audit.35076.json`. Promotion and
    archive-wide mapping claims remain false. Verification: 9 focused tests;
    targeted type checking, Ruff, JSON/schema checks, and Conductor review
    passed; full suite 358 passed, 2 skipped.
- [ ] Freeze the empirical sample, dual-annotate, adjudicate, and evaluate reliability.
  - `BLOCKED 2026-07-16`: a hash-pinned candidate sampling and annotation
    protocol now exists, but it is not human-approved. No authentic frozen unit
    manifest, duplicate-cluster registry, dual-annotation records, adjudication
    decisions, or agreement outputs exist. Completion requires a rights-approved
    source population, protocol approval, an approved codebook and sampling
    configuration, at least two independent human annotators, and a distinct
    adjudicator. No sample membership, labels, adjudication outcome, or
    reliability statistic may be inferred from contract fixtures.
  - [x] Protocol-preparation subtask: add the candidate protocol at
    `docs/41-v2-sampling-and-annotation-protocol.md` (SHA-256 `9747b22c…`) and a
    fail-closed review-readiness packet (`d2ea156`). Verification: 13 focused
    tests; Ruff, JSON/schema checks, and Conductor review passed; full suite
    364 passed, 2 skipped. Approval, role identities, population, codebook, and
    sampling configuration remain missing.
- [ ] Generate a versioned release-evidence bundle containing tag/SHA, contract
  versions, capabilities, tests, fixtures, provenance, empirical results,
  exceptions, migrations, and limitations.
  - `BLOCKED 2026-07-16`: there is no eligible immutable release target because
    empirical comparison, historical source/right review, correspondence-backed
    state mapping, independent fixture promotion, and empirical annotation,
    adjudication, and reliability evaluation remain incomplete. The bounded
    one-record governed reproducibility run is complete. A readiness checkpoint
    must not be presented as the required release-evidence bundle.
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
