# Plan: Ontology methods protocol

## Phase 1: Evidence inventory and protocol scaffold

- [ ] Task: Verify publication quality panel dependency
    - [ ] Confirm `publication_quality_panel_20260702` is archived as complete or explicitly approved as a dependency override.
    - [ ] Confirm scorecard, panel-review, and checklist contracts exist.
    - [ ] Stop and record a bounded blocker if the dependency is incomplete.
- [ ] Task: Catalogue repo-local ontology development evidence
    - [ ] Review `README.md`, `docs/00-repo-charter.md`, `docs/01-foundations-register.md`, `docs/02-system-architecture.md`, `docs/08-roadmap.md`, `docs/09-backlog.md`, `docs/11-implementation-status.md`, `docs/19-release-readiness-evidence.md`, `docs/22-semantic-alignment.md`, schemas, ontology, SHACL, vocab, mappings, prompts, examples, tests, and Conductor archive records.
    - [ ] Produce `docs/24-ontology-methods-evidence-inventory.md` as the bounded evidence inventory for protocol inputs.
    - [ ] Produce `docs/24-ontology-claims-register.md` with supported claims, repo-local evidence, unsupported claims, and external gates.
    - [ ] Produce `docs/24-ontology-terminology-crosswalk.md` for source states, FOI-O states, event types, assertion statuses, legal-source terms, validation surfaces, and certification terms.
    - [ ] Mark live-source and publication-only dependencies as external gates.
- [ ] Task: Write protocol structure tests first
    - [ ] Add a focused test requiring `docs/24-ontology-methods-protocol.md`.
    - [ ] Require headings for objectives, materials, ontology-development method, validation, governance, limitations, reproducibility, and planned analysis.
    - [ ] Require referenced repo-local paths, the evidence inventory, and the claims register to exist.
- [ ] Task: Draft the protocol scaffold
    - [ ] Create `docs/24-ontology-methods-protocol.md`.
    - [ ] Include the required headings and evidence inventory references.
    - [ ] Keep claims aligned with repo-local proof.
- [ ] Task: Establish publication source register
    - [ ] Create a source/bibliography register with repo-local evidence, external background sources, legal/guidance sources, and future journal-instruction sources.
    - [ ] Record retrieval dates where sources are external.
    - [ ] Mark whether each source can support claims, background context, legal provenance, or journal formatting only.
- [ ] Task: Specify publication visual/data assets
    - [ ] Define the ontology/evidence network model for Cosmograph-compatible node and edge data.
    - [ ] Define required static fallback diagrams for publication and accessibility.
    - [ ] Define required tables and plots for inventory counts, validation coverage, claim support, and external gates.
    - [ ] Define a generated-asset manifest contract with filename, asset type, caption, alt text/textual equivalent, source inputs, generation command, and provenance.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Evidence inventory and protocol scaffold' (Protocol in workflow.md)

## Phase 2: Methods development and validation detail

- [ ] Task: Expand ontology-development methods
    - [ ] Describe domain scoping and source selection.
    - [ ] Describe concept extraction, request/profile modelling, event/state modelling, and vocabulary design.
    - [ ] Describe schema, RDF/OWL, SKOS, SHACL, JSON-LD, and provenance alignment.
    - [ ] Describe how visual assets, plots, and tables are generated from repo-local sources rather than manual interpretation.
- [ ] Task: Document quality gates and human boundaries
    - [ ] Describe schema validation, example validation, SHACL validation, quality gates, event evaluation, release checks, and Conductor review evidence.
    - [ ] Document non-legal-advice and human-certification boundaries.
    - [ ] Label degraded-mode and optional dependency behavior.
- [ ] Task: Define supplementary-material contract
    - [ ] Specify which protocol details, evidence tables, visual assets, and reproducibility commands must appear in the final supplement.
    - [ ] Specify the supplement generation inputs consumed by `journal_submission_package_20260702`.
    - [ ] Require the supplement to include or link the generated-asset manifest.
    - [ ] Record journal-specific formatting as deferred until the journal target is selected.
- [ ] Task: Add prose and citation review gates
    - [ ] Run or document SourceRight-style checks for legal/guidance source provenance, unsupported claims, and citation/source boundaries.
    - [ ] Run or document AuthenText-style checks for manuscript-facing prose without altering technical literals.
    - [ ] Record any remaining review issues in the claims register.
- [ ] Task: Verify protocol consistency
    - [ ] Run focused protocol tests.
    - [ ] Run `uv run python scripts/validate_examples.py`.
    - [ ] Run Ruff checks on touched tests/scripts.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Methods development and validation detail' (Protocol in workflow.md)

## Phase 3: Protocol readiness

- [ ] Task: Harden publication-quality prose
    - [ ] Check terminology, caveats, and evidence claims.
    - [ ] Remove duplicated or stale status language.
    - [ ] Ensure the protocol can feed the results/report and journal-submission tracks.
- [ ] Task: Run publication panel review loop for protocol artifacts
    - [ ] Ask required panel agents to score the protocol, evidence inventory, claims register, terminology crosswalk, visual asset contract, and supplement contract out of 100.
    - [ ] Record scorecards and actionable findings using the panel contracts.
    - [ ] Apply high-confidence fixes and rerun scoring until every required score is greater than 95/100 or a bounded blocker is recorded.
    - [ ] Run checklist adherence checks applicable to the protocol and methods description.
- [ ] Task: Final repo-local verification
    - [ ] Run `uv run pytest -q`.
    - [ ] Run `uv run ruff check src tests scripts`.
    - [ ] Run `uv run ruff format --check src tests scripts`.
    - [ ] Run available Pixi/Mojo checks or record unavailable external gates.
    - [ ] Run `conductor-review` if available and apply high-confidence fixes.
- [ ] Task: Archive completed track
    - [ ] Mark metadata as completed.
    - [ ] Move the track to `conductor/archive/ontology_methods_protocol_20260702/`.
    - [ ] Update `conductor/tracks.md`.
    - [ ] Commit, attach git notes, and push commits/notes if remote access is available.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Protocol readiness' (Protocol in workflow.md)
