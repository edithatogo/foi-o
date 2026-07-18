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
- [x] Populate and review NZ historical source packs and the source-rights registry.
  - `COMPLETED 2026-07-17`: authoritative rights evidence, the complete
    50-version OIA PDF sequence, and 50 deterministic candidate event-time
    intervals are hash-pinned. Reviewer `edithatogo` has approved every
    inclusive/exclusive boundary against the relevant commencement and
    amendment evidence. The provider-scope registry is already approved. Seven
    official non-legislation guidance artifacts are locally stored and
    hash-pinned. Reviewer `edithatogo` has approved PSC-owned
    `publicservice.govt.nz` content subject to attribution and every recorded
    exclusion. Reviewer `edithatogo` has approved the seven-source selection and
    recorded historical applicability without expanding source rights.
    Reviewer `edithatogo` approved metadata-only source-pack promotion. Source
    contents remain local-only and uncommitted; redistribution, publication,
    release, and dataset publication remain prohibited. Older schema-valid
    examples remain contract fixtures, not evidence.
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
  - [x] Interval-approval subtask: record reviewer `edithatogo`'s exact legal
    review of all 50 hash-pinned candidate boundaries in a separate immutable
    artifact without modifying the candidate file or authorizing source-pack
    promotion, publication, release, dataset publication, or broader legal
    certification (`afc3378`). Output:
    `examples/v2/nz-oia-applicability-interval-review.approved.json` (SHA-256
    `90c3ee2a…`). Verification: 25 focused tests including candidate-hash and
    scope-expansion rejection; examples validation, scoped Ruff lint/format,
    and Conductor review passed; full suite 409 passed, 2 skipped.
  - [x] Non-legislation evidence subtask: acquire and independently verify two
    Ombudsman guide revisions, four Public Service Commission agency-guidance
    documents, and one PSC reporting-guidance document in local-only storage
    (`c78c47c`). Output:
    `examples/v2/nz-nonlegislation-source-manifest.2026-07-16.json` (SHA-256
    `4650961b…`). The Archives NZ candidate was excluded after direct retrieval
    returned only an anti-bot shell. Ombudsman personal-use scope is preserved;
    PSC provider scope, historical applicability, source selection, and
    source-pack promotion remain pending. Verification: all seven byte sizes,
    PDF signatures, and SHA-256 hashes reproduced; 19 focused tests, examples
    validation, and targeted Ruff passed; full suite 372 passed, 2 skipped.
  - [x] PSC provider-scope approval subtask: record reviewer `edithatogo`'s
    exact approval of provider-owned `publicservice.govt.nz` content, pinned to
    terms evidence `2ad002bf…`, while preserving every exclusion, attribution
    requirement, and downstream publication/promotion prohibition (`6b2fb0b`).
    Output: `examples/v2/psc-provider-scope-review.approved.json` (SHA-256
    `dcb8179c…`). Verification: 29 focused tests including negative terms-hash,
    exclusion, and publication cases; examples validation, Ruff lint/format,
    and Conductor review passed; full suite 413 passed, 2 skipped.
  - [x] Seven-source approval subtask: record reviewer `edithatogo`'s exact
    selection and historical-applicability approval for manifest `4650961b…`
    without expanding rights or authorizing promotion or publication
    (`0801737`). Output:
    `examples/v2/nz-nonlegislation-source-review.approved.json` (SHA-256
    `68a27725…`). Verification: 34 focused tests including negative manifest,
    rights, and promotion cases; examples validation, Ruff checks, and
    Conductor review passed; full suite 418 passed, 2 skipped.
  - [x] Metadata-only source-pack promotion subtask: bind reviewer
    `edithatogo`'s approval of readiness `a2ceffc2…`, materialize a governed pack
    containing references and digests only, and prohibit source bytes,
    redistribution, publication, release, and dataset publication (`943b100`).
    Output: `examples/v2/nz-source-pack.governed-metadata.json`. Verification:
    two independent agent reviews; 40 focused tests including source-content,
    attribution, exclusion, digest, and publication drift; full suite 424
    passed, 2 skipped.
- [ ] Audit FYI raw-state mappings against correspondence and attachments.
  - `BLOCKED 2026-07-17`: approved request `35076` supplies one real outgoing
    correspondence item for the bounded candidate mapping `waiting_response` to
    `awaiting_response`, with an empty attachment inventory. Reviewer
    `edithatogo` has now approved exact pending request `11872` manifest
    `42f8ed87…` and its separately declared rendered-HTML supplement for the
    local raw-state mapping audit only. The resulting approved manifest
    `0c7cee55…` verifies four correspondence blocks and three local PDFs, and
    supports the bounded candidate mapping `partially_successful` to
    `released_in_part`. Reviewer `edithatogo` has approved that mapping for
    request `11872` only. Reviewer `edithatogo` has also approved the bounded
    request `35076` mapping `waiting_response` to `awaiting_response`, preserving
    its empty attachment inventory. Archive-wide evidence remains required; no
    legal certification, redistribution, publication, training, release,
    dataset, or reviewed/gold promotion is authorized.
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
  - [x] Attachment-snapshot candidate subtask: capture request `11872` with
    clean `fyi-cli` revision `c91e49d`, preserve its empty canonical JSON
    attachment inventory, separately declare three attachment links recovered
    from hash-pinned rendered HTML, and verify every local byte (`ff7a99b`). The
    pending manifest SHA-256 is `42f8ed87…`; four correspondence blocks and
    13,259,266 PDF bytes verify. New verifier coverage is 81.86%; 25 focused
    tests, examples validation, targeted Ruff and type checks passed; full suite
    392 passed, 2 skipped. Exact snapshot rights, supplemental-capture review,
    mapping review, and archive-wide evidence remain pending.
  - [x] Attachment-approval integrity subtask: require any approved bundle to
    verify the exact reviewed pending manifest and reproduce every non-rights
    artifact hash and size (`43578ef`). Missing reviewed evidence or content
    drift fails closed. Verification: actual pending manifest `42f8ed87…`
    remained unchanged; new module coverage 82.01%; 26 focused tests and
    targeted Ruff/type checks passed; full suite 393 passed, 2 skipped.
  - [x] Approved attachment audit subtask: bind reviewer `edithatogo`'s exact
    approval of pending manifest `42f8ed87…` to a separate immutable local
    bundle, verify all reviewed bytes, and produce a bounded request `11872`
    raw-state audit without widening the approved purpose or publication rights
    (`53bcfb2`). Verification: 38 focused tests; attachment module coverage
    80.37%; example validation, scoped Ruff lint/format, type checks, and
    Conductor review passed; full suite 395 passed, 2 skipped. Review replaced
    class-order-dependent direction counts with HTML-parser counts.
  - [x] Bounded mapping approval subtask: record reviewer `edithatogo`'s exact
    request `11872` approval as a separate hash-pinned review artifact without
    modifying the candidate audit, approving request `35076`, or enabling an
    archive-wide claim or any prohibited downstream use (`9eac898`). Output:
    `examples/v2/bounded-raw-state-mapping-review.11872.json` (SHA-256
    `bfa25427…`). Verification: 27 focused tests including four negative
    scope-expansion cases; examples validation, scoped Ruff lint/format, and
    Conductor review passed; full suite 401 passed, 2 skipped.
  - [x] Bounded request `35076` mapping approval subtask: record reviewer
    `edithatogo`'s exact approval in a separate hash-pinned review artifact,
    without treating its empty attachment inventory as archive-wide evidence or
    enabling legal certification or any prohibited downstream use (`1052dbc`).
    Output: `examples/v2/bounded-raw-state-mapping-review.35076.json` (SHA-256
    `a2125c4b…`). Verification: 30 focused tests including scope-expansion and
    cross-request evidence rejection; examples validation, scoped Ruff
    lint/format, and Conductor review passed; full suite 404 passed, 2 skipped.
- [ ] Freeze the analyst sample, run independent dual analysis, reconcile, and
  evaluate inter-analyst agreement.
  - [x] Analyst-protocol reframing subtask: supersede the human-only execution
    design with a versioned role-neutral protocol in which two independent
    analysts and a distinct reconciler may be automated agents, with explicit
    actor provenance, isolation, immutable locks, and claim-class boundaries.
    Preserve the prior hash-approved protocol as historical v0.1 evidence;
    agent-derived outputs must not be described as human-reviewed or promoted
    to gold, legal certification, publication, dataset, or release status
    without their separately required gates (`b46ca78`). Verification: 4 new
    contract tests, focused empirical/schema suite 72 passed, repository
    inventory checks 14 passed, Ruff and JSON checks passed, and full suite 462
    passed, 2 skipped. The exact v0.1 protocol SHA-256 remains `3620198f…`.
  - `ACTIVE 2026-07-17`: the v0.2 analyst protocol permits separately authorized
    bounded local agent execution in principle. The exact fixture rights and
    execution inputs are now approved and promoted, but no concrete roles,
    execution authorization, analysis sets, reconciliation decisions, or
    diagnostics exist. Agent results remain non-human-reviewed, non-gold,
    non-release-qualifying, and non-publication-eligible.
  - [x] Fixture-only execution-packet subtask: construct the candidate v0.2
    fixture inputs and readiness artifact only—an exact committed synthetic
    population, dedicated candidate codebook, deterministic sampling
    configuration, unit/redaction/cluster manifests, and pending rights review.
    Bounded rights and input approval are the next gate. Concrete analyst and
    reconciler roles plus execution authorization require a later, separately
    committed and hash-approved v0.2 authorization before any analysis
    (`948d392`). Output:
    `examples/v2/analyst-fixture-packet/readiness.json`, SHA-256
    `de4bdf129f433373b1287c78867db51b1874bd33476dd2229e0710dfc25e03bd`.
    Verification: deterministic regeneration and all eight nested schema checks;
    35 focused tests; verifier coverage 84%; BasedPyright and scoped Ruff clean;
    two independent peer reviews plus orchestrated review passed; full suite 493
    passed, 2 skipped. Rights/input approval, concrete roles, execution
    authorization, analysis, reconciliation, and diagnostics remain absent.
  - [x] Fixture rights/input approval-promotion subtask: record `edithatogo`'s
    exact bounded approval of readiness SHA-256 `de4bdf129…` at implementation
    commit `948d392`, preserve the approved candidate bytes, and derive a new
    committed approved-input set with rights-eligible units and dependent hashes.
    Keep execution disabled; concrete roles and v0.2 execution authorization
    remain a later separate exact human gate (`fe875ab`). Output:
    `examples/v2/analyst-fixture-packet/input-readiness.approved.json`, SHA-256
    `814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e`.
    Verification: exact approval-statement SHA-256 `48a0f550…`; deterministic
    seven-artifact promotion; historical base and final Git anchors; 45 focused
    tests; BasedPyright and Ruff clean; two independent peer reviews plus
    orchestrated review passed; full suite 503 passed, 2 skipped; post-commit
    verifier passed against promotion commit `fe875ab`. Roles remain unassigned;
    execution authorization is absent and `execution_allowed` remains false.
  - [x] Pending role-authorization preparation subtask: bind the four fresh,
    readiness-only canonical session locators, exact role prompts, redacted
    context presentation, isolation rules, approved-input readiness, and output
    boundaries in a committed request with execution disabled. Runtime UUIDs
    and exact model snapshots are unavailable and must remain explicitly
    unavailable; no analysis begins before separate hash-bound human approval
    (`91013a0`). Output:
    `examples/v2/analyst-fixture-packet/role-authorization-request.pending.json`,
    SHA-256
    `232396d06812e6158a86aec38454d7e3ea8484ed906bf510c39976993c29a98c`.
    Verification: exact canonical prompt/actor enforcement; safe paths and full
    historical/final Git anchors; independent 11-context rederivation; 32
    focused tests; three read-only reviews passed; full suite 525 passed, 2
    skipped; post-commit request verifier passed against `91013a0`. Human
    approval, execution authorization, content presentation, and all handshakes
    remain absent; `execution_allowed` remains false.
  - [x] Runtime-handshake authorization subtask: record `edithatogo`'s exact
    approval of request SHA-256 `232396d0…` at commit `91013a0`, create a
    separately pinned handshake-only authorization, and require successful
    verification against its exact committed SHA before presenting only the
    runtime-provenance handshake prompt. Context presentation, analysis, and
    reconciliation remain disabled. Four committed runtime-handshake evidence
    records, a final v0.2 execution-authorization candidate, its separate exact
    human approval, and successful pre-execution verification remain absent
    (`c41f514`). Output:
    `examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json`,
    SHA-256
    `de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f`.
    Verification: exact approval-statement SHA-256 `29cf6248…`; full historical
    DAG and commit-ancestry checks; 78 focused governance tests; Ruff lint and
    format clean; task-scoped `ty` clean; full suite 549 passed, 2 skipped;
    three independent reviews passed; post-commit verifier passed against exact
    commit `c41f514a9707f48286fd238fc2140085cceff648`. Repository-wide `ty`
    retains 51 diagnostics identical to pre-task `3531022`; no task-introduced
    diagnostics remain. A test-only post-commit clone-harness repair (`c5ae291`)
    preserves deterministic HEAD reuse and real descendant mutation commits;
    the full suite remains 549 passed, 2 skipped. Only the canonical
    runtime-provenance handshake may now be presented; fixture contexts and all
    analysis remain prohibited.
  - [x] Protocol-preparation subtask: add the candidate protocol at
    `docs/41-v2-sampling-and-annotation-protocol.md` (current SHA-256
    `3620198f…`) and a
    fail-closed review-readiness packet (`d2ea156`). Verification: 13 focused
    tests; Ruff, JSON/schema checks, and Conductor review passed; full suite
    364 passed, 2 skipped. Approval, role identities, population, codebook, and
    sampling configuration remain missing.
  - [x] Protocol operational-alignment subtask: correct duplicate-cluster split
    semantics, align the primary assertion-level unit, require unit/cluster
    digests, and pre-register span, abstention, confidence-interval, kappa, and
    extractor-matching rules (`5f483fd`). Verification: 12 focused tests,
    examples validation, Ruff, and full suite 426 passed, 2 skipped. This does
    not approve the protocol or supply human roles or execution inputs.
  - [x] Protocol approval subtask: record `edithatogo`'s exact bounded approval
    of protocol SHA-256 `3620198f…` in a separate review artifact, remove only
    the protocol-review blocker, and preserve every sample, label,
    adjudication, empirical-result, gold-promotion, publication, release, and
    dataset-publication prohibition (`5e91540`). Verification: 18 focused
    tests, Ruff, BasedPyright, exact hash/schema checks, and full suite 454
    passed, 2 skipped. Human roles and execution inputs remain missing.
  - [x] Duplicate-cluster contract subtask: add a strict registry schema with
    population and algorithm pins, one split per cluster, and distinct
    candidate-fixture versus authentic frozen-evidence states (`3591647`).
    Verification: 2 focused tests, Ruff, and full suite 428 passed, 2 skipped.
    No authentic registry or sample membership was created.
  - [x] Empirical unit-freeze contract subtask: define immutable unit/source
    hashes and spans, request linkage, duplicate-cluster membership, splits,
    strata, probability/enrichment provenance, inclusion probabilities,
    weights, accessibility, and rights eligibility with distinct candidate and
    authentic frozen states (`29592da`). Verification: 7 focused tests, Ruff,
    exact inventory checks, and full suite 442 passed, 2 skipped. No authentic
    unit membership or sample freeze was created.
  - [x] Locked-annotation contract subtask: require unit/codebook pins,
    candidate blinding, reviewer identity, half-open spans, uncertainty,
    abstention, timestamps, and immutable lock provenance, while rejecting
    agent identities for authentic human annotations (`3395dc1`). Verification:
    2 focused tests, Ruff, and full suite 430 passed, 2 skipped. No annotation
    record or empirical evidence was created.
  - [x] Adjudication contract subtask: preserve both locked annotation hashes
    and reviewer identities, require a human-form adjudicator identity,
    reasoned resolved/unresolved outcomes, and immutable lock provenance while
    rejecting agent adjudicators (`f7aec30`). Verification: 2 focused tests,
    Ruff, and full suite 432 passed, 2 skipped. No adjudication occurred.
  - [x] Reliability-report contract subtask: pin the protocol, sample,
    duplicate-cluster registry, two annotation sets, adjudication set, and
    codebook; require explicit denominators, two-sided cluster-bootstrap
    configuration, registered kappa undefined reasons, span agreement, and
    adjudication/unresolved rates while prohibiting fixture promotion
    (`3b65fa7`). Verification: 8 focused schema tests, Ruff, exact inventory
    checks, and full suite 436 passed, 2 skipped. No reliability statistic was
    calculated.
  - [x] Empirical cross-artifact verifier subtask: recompute file and record
    hashes; require authentic frozen units and clusters, two distinct human
    annotators and a distinct human adjudicator, exact unit/cluster/split and
    adjudication-reference consistency, codebook alignment, lock chronology,
    agreement/statistic recomputation, explicit accounting, and permanently
    disabled promotion (`1702e35`). Verification: Ruff, BasedPyright, 7 focused
    tests at 94% coverage, and full suite 449 passed, 2 skipped. Synthetic test
    bundles are temporary and explicitly non-evidentiary; no authentic bundle
    or empirical result exists.
  - [x] Execution-authorization contract subtask: bind protocol, source
    population, codebook, sampling configuration, exactly two human annotator
    roles, a human adjudicator role, and a named human approver in distinct
    pending and approved states while explicitly prohibiting agents from human
    roles (`92ed642`). Verification: Ruff, BasedPyright, 7 focused tests, exact
    inventory checks, and full suite 452 passed, 2 skipped. No approved
    authorization or role assignment exists.
  - [x] Execution-input contract subtask: govern a rights-reviewed source
    population with retained exclusions, an annotation codebook with label and
    disagreement semantics, and a sampling configuration with sample-size,
    strata, inclusion-probability, weighting, clustering, exclusion, split,
    and bootstrap pins (`469a80b`). Verification: Ruff, BasedPyright, 8 focused
    tests, exact schema/inventory checks, and full suite 458 passed, 2 skipped.
    No concrete input was created or approved.
  - [x] Execution-authorization enforcement subtask: require the exact approved
    authorization bytes and hashes for the protocol, source population,
    codebook, and sampling configuration; require authorized annotator and
    adjudicator identities and codebook revision; and require approval to
    precede unit-manifest creation (`9c3f90a`). Verification: Ruff,
    BasedPyright, 14 focused contract tests, verifier coverage 94%, and full
    suite 452 passed, 2 skipped. No actual authorization exists.
  - [x] Annotation-outcome hardening subtask: require controlled abstention
    reasons, require labels for non-abstaining annotations, and require labels
    for resolved adjudications so missing evidence and unresolved outcomes
    cannot be silently converted into empirical labels (`ace9e12`).
    Verification: 11 focused schema tests, Ruff, and full suite 439 passed,
    2 skipped. Task-conditioned span checks and cross-artifact consistency
    remain verifier responsibilities; no annotation or adjudication occurred.
  - [x] Consolidated human-gate packet subtask: pin the interval, PSC provider
    scope, seven-source selection, source-pack promotion, bounded raw-state
    mapping, and annotation-protocol decisions in
    `examples/v2/empirical-human-gate-review-packet.pending.json` (`ec4573b`,
    expanded with attachment-snapshot review in `ff7a99b`; current SHA-256
    `19e66fb6…`, subsequently updated by the approved review artifacts). OIA
    intervals, PSC scope, seven-source selection/applicability, metadata-only
    source-pack promotion, attachment rights, and both bounded raw-state
    mappings are approved. Annotation protocol approval, human roles, source
    population, codebook, and sampling configuration remain missing;
    sample-freeze and empirical-comparison gates remain false.
- [ ] Generate a versioned release-evidence bundle containing tag/SHA, contract
  versions, capabilities, tests, fixtures, provenance, empirical results,
  exceptions, migrations, and limitations.
  - `BLOCKED 2026-07-17`: there is no eligible immutable release target because
    empirical comparison, independent fixture promotion, and empirical
    annotation, adjudication, and reliability evaluation remain incomplete.
    Historical source/right review, metadata-only source-pack promotion, both
    bounded correspondence-backed mappings, and the one-record governed
    reproducibility run are complete. A readiness checkpoint must not be
    presented as the required release-evidence bundle.
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
