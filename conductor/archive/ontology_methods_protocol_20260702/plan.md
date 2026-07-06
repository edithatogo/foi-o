# Plan: Ontology methods protocol

## Phase 1: Evidence inventory and protocol scaffold

- [x] Task: Verify publication quality panel dependency
    - [x] Confirm `publication_quality_panel_20260702` is archived as complete or explicitly approved as a dependency override.
    - [x] Confirm scorecard, panel-review, and checklist contracts exist.
    - [x] Stop and record a bounded blocker if the dependency is incomplete.
- [ ] Task: Catalogue repo-local ontology development evidence
    - [ ] Review `README.md`, `docs/00-repo-charter.md`, `docs/01-foundations-register.md`, `docs/02-system-architecture.md`, `docs/08-roadmap.md`, `docs/09-backlog.md`, `docs/11-implementation-status.md`, `docs/19-release-readiness-evidence.md`, `docs/22-semantic-alignment.md`, schemas, ontology, SHACL, vocab, mappings, prompts, examples, tests, and Conductor archive records.
    - [ ] Produce `docs/24-ontology-methods-evidence-inventory.md` as the bounded evidence inventory for protocol inputs.
    - [ ] Produce `docs/24-ontology-claims-register.md` with supported claims, repo-local evidence, unsupported claims, and external gates.
    - [ ] Produce `docs/24-ontology-terminology-crosswalk.md` for source states, FOI-O states, event types, assertion statuses, legal-source terms, validation surfaces, and certification terms.
    - [ ] Mark live-source and publication-only dependencies as external gates.
- [x] Task: Write protocol structure tests first
    - [x] Add a focused test requiring `docs/24-ontology-methods-protocol.md`.
    - [x] Require headings for objectives, materials, ontology-development method, validation, governance, limitations, reproducibility, and planned analysis.
    - [x] Require referenced repo-local paths, the evidence inventory, and the claims register to exist.
- [x] Task: Draft the protocol scaffold
    - [x] Create `docs/24-ontology-methods-protocol.md`.
    - [x] Include the required headings and evidence inventory references.
    - [x] Keep claims aligned with repo-local proof.
- [x] Task: Establish publication source register
    - [x] Create a source/bibliography register with repo-local evidence, external background sources, legal/guidance sources, and future journal-instruction sources.
    - [x] Record retrieval dates where sources are external.
    - [x] Mark whether each source can support claims, background context, legal provenance, or journal formatting only.
- [x] Task: Specify publication visual/data assets
    - [x] Define the ontology/evidence network model for Cosmograph-compatible node and edge data.
    - [x] Define required static fallback diagrams for publication and accessibility.
    - [x] Define required tables and plots for inventory counts, validation coverage, claim support, and external gates.
    - [x] Define a generated-asset manifest contract with filename, asset type, caption, alt text/textual equivalent, source inputs, generation command, and provenance.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Evidence inventory and protocol scaffold' (Protocol in workflow.md)

## Phase 2: Methods development and validation detail

- [x] Task: Expand ontology-development methods
    - [x] Describe domain scoping and source selection.
    - [x] Describe concept extraction, request/profile modelling, event/state modelling, and vocabulary design.
    - [x] Describe schema, RDF/OWL, SKOS, SHACL, JSON-LD, and provenance alignment.
    - [x] Describe how visual assets, plots, and tables are generated from repo-local sources rather than manual interpretation.
- [x] Task: Document quality gates and human boundaries
    - [x] Describe schema validation, example validation, SHACL validation, quality gates, event evaluation, release checks, and Conductor review evidence.
    - [x] Document non-legal-advice and human-certification boundaries.
    - [x] Label degraded-mode and optional dependency behavior.
- [x] Task: Define supplementary-material contract
    - [x] Specify which protocol details, evidence tables, visual assets, and reproducibility commands must appear in the final supplement.
    - [x] Specify the supplement generation inputs consumed by `journal_submission_package_20260702`.
    - [x] Require the supplement to include or link the generated-asset manifest.
    - [x] Record journal-specific formatting as deferred until the journal target is selected.
- [x] Task: Add prose and citation review gates
    - [x] Run or document SourceRight-style checks for legal/guidance source provenance, unsupported claims, and citation/source boundaries.
    - [x] Run or document AuthenText-style checks for manuscript-facing prose without altering technical literals.
    - [x] Record any remaining review issues in the claims register.
- [x] Task: Verify protocol consistency
    - [x] Run focused protocol tests.
    - [x] Run `uv run python scripts/validate_examples.py`.
    - [x] Run Ruff checks on touched tests/scripts.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Methods development and validation detail' (Protocol in workflow.md)

## Phase 3: Protocol readiness

- [x] Task: Harden publication-quality prose
    - [x] Check terminology, caveats, and evidence claims.
    - [x] Remove duplicated or stale status language.
    - [x] Ensure the protocol can feed the results/report and journal-submission tracks.
- [x] Task: Run publication panel review loop for protocol artifacts
    - [x] Ask required panel agents to score the protocol, evidence inventory, claims register, terminology crosswalk, visual asset contract, and supplement contract out of 100.
    - [x] Record scorecards and actionable findings using the panel contracts.
    - [x] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [x] Run checklist adherence checks applicable to the protocol and methods description.
- [x] Task: Final repo-local verification
    - [x] Run `uv run pytest -q`.
    - [x] Run `uv run ruff check src tests scripts`.
    - [x] Run `uv run ruff format --check src tests scripts`.
    - [x] Run available Pixi/Mojo checks or record unavailable external gates.
    - [x] Run `conductor-review` if available and apply high-confidence fixes.
- [x] Task: Archive completed track
    - [x] Mark metadata as completed.
    - [x] Move the track to `conductor/archive/ontology_methods_protocol_20260702/`.
    - [x] Update `conductor/tracks.md`.
    - [x] Commit, attach git notes, and push commits/notes if remote access is available.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Protocol readiness' (Protocol in workflow.md)
