# Implementation Plan

## Phase 1: Establish the cross-track gate map

- [x] Create the umbrella track with dependency and human-gate metadata.
      (`current track setup`)
- [x] Link NZ payload/rights, Australian source/rights, AU-CTH fresh-holdout,
      and release authorization evidence. (`54dee35`, `857926b`, `c9155d6`)
- [x] Preserve fail-closed statuses for every unresolved external or human gate.
      (`current track setup`)
- [x] Create a dependency-ordered six-gate resolution playbook with options,
      contingencies, trade-offs, evidence contracts, and approval boundaries.
      (`9612f08`)

## Phase 2: Maintain source and rights boundaries

- [x] Record NZ authentic-content rights packet and metadata-only limitation.
      (`443d682`)
- [x] Record seven-jurisdiction Australian source/rights evidence register.
      (`857926b`)
- [ ] Obtain exact item-level rights decisions for approved source fixtures.
- [ ] Resolve QLD registration, terms, and credential custody.
- [ ] Decide whether any mirror is permitted only as an independent oracle.
- [x] Before operational mirror use, add a `mirror_comparator` contract role
      and tests proving mirrors cannot control authority or satisfy minimum
      supporting-source counts. (`4ba46ea`)

## Phase 3: Resolve empirical prerequisites

- [ ] Recover exact NZ payloads or obtain approval for a provenance-complete
      replacement.
- [x] Reconcile the stale 10,000-row AU-CTH candidates and earlier retrieval
      pin against the completed 26,000-record CDX evidence before frame work.
      (`7786350`)
- [ ] Resolve AU-CTH replay compatibility, failure-ledger evidence, fresh-frame
      approval, and execution authorization.
- [ ] Run empirical work only after the exact upstream gates are satisfied.

## Phase 4: Release governance

- [x] Create destination-specific release/publication authorization packet.
      (`c9155d6`)
- [x] Reconcile the historical publication packet's superseded execution-check
      section with its later verified Zenodo and OSF receipts. (`f35b099`)
- [x] Freeze an exact release manifest and complete integrity/rights review.
      (`978f88a`)
      - Semantic-core self-pin:
        `729be73762c28421130595cb587c441fa1f230e136746410a10b241b9a3d9fa4`
        at target `d7c4cb1726fc7dcbb16b06014dc07218ea6220ec`.
      - Serialized manifest SHA-256:
        `460d42a0f392c1d11f6daedfcdaf7099ed872e68eebc00d8a69edd9b6faebfb0`.
      - Independent integrity and rights/public-scope reviews pass; release and
        publication remain unauthorized.
      - Review: `conductor/release-candidate-2026-08-03/review.md`.
- [x] Rebase the repository-owned release prerequisites onto current `main` in
      an isolated branch, validate deterministic destination-neutral archive
      construction, and regenerate all commit-bound candidate evidence.
      (`81b78c5`, `154c64f`, `1993b54`, `04ed03c`, `ef591fa`, `d51d5ac`)
- [x] Obtain destination-specific authorization and verify one destination at
      a time. (`GitHub release verified 2026-08-20; see
      github-semantic-core-release-receipt-2026-08-20.md`; `a5d2a98`)

## Review and completion boundary

- [ ] Run whole-track review after repository-owned tasks are complete.
- [ ] Archive only after all acceptance gates are satisfied; external gates do
      not become satisfied from local validation.

## Current blocker disposition

The remaining unchecked tasks are intentionally external or human-gated. Local
validation, prior destination receipts, metadata-only approvals, and bounded
historical maturity decisions do not satisfy them. The track must remain in
progress until exact evidence or approvals are recorded.
