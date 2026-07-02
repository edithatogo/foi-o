# Supplement: FOI-O NZ Ontology and Validation Package

## S1. Scope

This supplement supports the manuscript
`docs/27-submission-manuscript.md`. It records the repository artefacts,
validation commands, boundaries, and generated-asset plan for the FOI-O NZ
submission package.

The supplement does not include live FYI/archive request payloads, legal advice,
agency-internal records, journal account uploads, or arXiv submission approval.

## S2. Repository Artefact Inventory

| Artefact class | Repo paths | Purpose |
| --- | --- | --- |
| JSON Schemas | `schemas/json/` | Machine-readable contracts for requests, events, agent actions, reports, release metadata, publication scorecards, and arXiv readiness. |
| Examples | `examples/` | Small deterministic fixtures for schema validation, publication metadata, release readiness, event evaluation, and package checks. |
| Python package | `src/foi_o_nz/` | Control plane for validation, normalisation, quality gates, reporting, RDF export, metadata, retrieval, and CLI workflows. |
| Tests | `tests/` | Repo-local evidence that contracts, examples, safety boundaries, and publication fixtures behave as expected. |
| Ontology | `ontology/foi-o-nz.ttl` | OWL/RDF seed for FOI-O NZ process concepts. |
| SHACL | `shacl/foi-o-nz.shapes.ttl` | Semantic validation and safety constraints. |
| SKOS vocabularies | `vocab/*.skos.ttl` | Controlled vocabularies for request states, event types, assertion status, and agent boundaries. |
| Mappings | `mappings/*.yaml` | FYI/Alaveteli state mapping, PSC reporting derivability, and legal-source reference metadata. |
| Publication docs | `docs/23-release-package.md`, `docs/26-journal-target-requirements.md`, `docs/30-arxiv-readiness.md` | Release, journal, and preprint readiness evidence. |

## S3. Validation Commands

The core repo-local validation sequence is:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
uv run python scripts/validate_examples.py
```

Publication-focused checks include:

```bash
uv run pytest -q tests/test_methods_paper.py
uv run pytest -q tests/test_publication_metadata.py
uv run pytest -q tests/test_publication_quality_panel.py
uv run pytest -q tests/test_release_package.py
```

Semantic checks include:

```bash
uv run pytest -q tests/test_rdf_export.py tests/test_semantic_alignment.py tests/test_shacl_safety_profiles.py
```

Native Mojo/MAX checks are external gates unless the local Modular/Pixi
toolchain is available:

```bash
pixi run mojo-format-check
pixi run mojo-test
pixi run mojo-build
```

## S4. Ontology and Standards Alignment

FOI-O NZ uses the canonical namespace
`https://w3id.org/foio-nz/ontology#`. The semantic layer aligns with:

- PROV-O for events, evidence, provider runs, review tasks, and derivation;
- SKOS for controlled vocabularies;
- DCAT for dataset and catalogue metadata;
- ODRL for publication and reuse constraints;
- legal-document identifiers for source-versioned statute and guidance
  references.

Semantic alignment is documented in `docs/22-semantic-alignment.md`.

## S5. Human Certification Boundary

Agents may:

- map observed FYI states to normalised process states;
- create candidate events from public manifests;
- calculate indicative clocks with warnings;
- draft search plans, summaries, and quality checks;
- prepare disclosure-log metadata and reporting extracts.

Agents must not certify:

- access or refusal decisions;
- redactions or releases;
- withholding grounds;
- public-interest balancing;
- charges;
- extensions or transfers where a statutory decision or notice is required;
- complaint or review outcomes.

This boundary is tested through agent-policy tests, quality-gate tests,
publication metadata tests, SHACL safety profiles, and example validation.

## S6. Generated Asset Plan

The final publication package should include generated diagrams, tables, plots,
and graph/network files. The current source package includes a text-renderable
architecture diagram in the manuscript and a committed Mermaid state-machine
example at `examples/state-machine.mmd`.

| Asset | Source input | Output target | Status |
| --- | --- | --- | --- |
| Architecture flow diagram | `docs/27-submission-manuscript.md` | Manuscript figure | Included as Mermaid source; static rendering pending final journal format. |
| State-machine diagram | `examples/state-machine.mmd` | Supplement figure | Source committed; static rendering pending final journal format. |
| Artefact inventory table | Repository file layout | Supplement table | Included. |
| Validation evidence table | `docs/19-release-readiness-evidence.md` | Manuscript table | Included. |
| Cosmograph node data | Ontology, schema, example, and validation relationships | Supplement graph data | Planned for results/report track; not yet generated. |
| Static graph fallback | Cosmograph node/edge data | Supplement figure | Planned for results/report track; not yet generated. |

Every final asset must have a caption, alt text or textual equivalent, source
input, generation command, provenance entry, and intended manuscript/supplement
location.

## S7. arXiv Source-Package Readiness

The arXiv source-package workflow is documented in `docs/30-arxiv-readiness.md`
and represented by `examples/arxiv-readiness.manuscript-planned.json`.

The default package workflow is:

1. generate LaTeX from the manuscript source;
2. compile with `latexmk` and TeX Live 2025 where available;
3. use `latexpand` when include flattening adds value;
4. use `arxiv-latex-cleaner` as the default sanitizer;
5. optionally run ALC-NG as a second-pass sanitizer if it preserves the compiled
   output;
6. scan the cleaned source package for secrets, local paths, comments, stale
   files, metadata, and font issues;
7. keep arXiv category selection, author metadata, declarations, and upload as
   human-only gates.

## S8. External Gates

The following items remain outside repo-local automation:

- live FYI/archive pulls;
- live publication registry deposits;
- Hugging Face, Zenodo, OSF, arXiv, or journal upload;
- final author list, affiliations, funding, conflicts, acknowledgements, and
  cover letter;
- external peer review and editorial acceptance;
- official government, Ombudsman, or PSC endorsement.

## S9. Reproducibility Notes

The release package records repeatable local evidence and external gates in:

- `docs/19-release-readiness-evidence.md`;
- `docs/23-release-package.md`;
- `examples/release-checklist.v0.9.0.json`;
- `examples/repository-release-metadata.v0.9.0.json`;
- `examples/arxiv-readiness.manuscript-planned.json`.

Passing repo-local checks means the committed repository artefacts validate
locally. It does not mean that a live source, registry, journal, or arXiv system
has accepted the package.
