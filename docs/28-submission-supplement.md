---
title: "Supplement: FOI-O Global Ontology and Jurisdiction Validation Package"
header-includes:
  - "\\usepackage{booktabs}"
  - "\\usepackage{array}"
  - "\\usepackage{longtable}"
  - "\\usepackage{caption}"
  - "\\usepackage{xurl}"
  - "\\setlength{\\emergencystretch}{3em}"
  - "\\sloppy"
---

# Supplement: FOI-O Global Ontology and Jurisdiction Validation Package

## S1. Scope

This supplement supports the manuscript
\path{docs/27-submission-manuscript.md}. It records the repository artefacts,
validation commands, boundaries, and generated-asset plan for the global FOI-O
submission package, which originated in New Zealand and has iterated through
Australian jurisdictions.

It also records the separate extraction-contract boundary, the wider programme
handoffs, and the candidate-only status of Australian jurisdiction adapters.

The supplement does not include live FYI/archive request payloads, legal advice,
agency-internal records, journal account uploads, or arXiv submission approval.

\clearpage

## S2. Repository Artefact Inventory

\begingroup
\small
\setlength{\tabcolsep}{2pt}
\begin{longtable}{>{\raggedright\arraybackslash}p{0.20\linewidth}>{\raggedright\arraybackslash}p{0.24\linewidth}>{\raggedright\arraybackslash}p{0.40\linewidth}}
\caption{Repository artefact inventory for the FOI-O NZ supplement. Abbreviations: FOI-O, Freedom of Information Ontology; NZ, New Zealand; JSON, JavaScript Object Notation; RDF, Resource Description Framework; BPMN, Business Process Model and Notation; PNML, Petri Net Markup Language; FYI, FYI.org.nz public request platform; PSC, Public Service Commission.}\\
\toprule
Artefact class & Repo paths & Purpose \\
\midrule
\endfirsthead
\caption[]{Repository artefact inventory for the FOI-O NZ supplement continued.}\\
\toprule
Artefact class & Repo paths & Purpose \\
\midrule
\endhead
JSON Schemas & \path{schemas/json/} & Machine-readable contracts for requests, events, agent actions, reports, release metadata, process-mining fixtures, empirical task-set planning, publication scorecards, and arXiv readiness. \\
Examples & \path{examples/} & Small deterministic fixtures for schema validation, publication metadata, release readiness, event evaluation, process-mining interchange, empirical task-set planning, and package checks. \\
Python package & \path{src/foi_o_nz/} & Control plane for validation, normalisation, quality gates, reporting, RDF export, metadata, retrieval, and command-line workflows. \\
Tests & \path{tests/} & Repo-local evidence that contracts, examples, safety boundaries, and publication fixtures behave as expected. \\
Ontology & \path{ontology/foi-o-nz.ttl} & OWL/RDF seed for FOI-O NZ process concepts. \\
SHACL & \path{shacl/foi-o-nz.shapes.ttl} & Semantic validation and safety constraints. \\
SKOS vocabularies & \path{vocab/*.skos.ttl} & Controlled vocabularies for request states, event types, assertion status, and agent boundaries. \\
Process models & \path{process_models/} & BPMN, PNML, and generated state-machine artefacts for workflow review and interchange. \\
Mappings & \path{mappings/*.yaml} & FYI/Alaveteli state mapping, PSC reporting derivability, and legal-source reference metadata. \\
Publication docs & \path{docs/23-release-package.md}, \path{docs/26-journal-target-requirements.md}, \path{docs/30-arxiv-readiness.md} & Release, journal, and preprint readiness evidence. \\
Empirical contracts & \path{src/foi_o_nz/empirical_contracts.py}, \path{src/foi_o_nz/contract_capabilities.py} & Capability declarations, immutable dependency requirements, evidence thresholds, and human promotion gates. \\
Jurisdiction profiles & \path{schemas/json/jurisdiction-source-pack.schema.json}, \path{examples/v2/schema-valid/}, \path{docs/39-ontology-versioning-and-jurisdiction-profiles.md} & Versioned core, country, and subdivision profile contracts; Australian examples remain candidate-only. \\
\bottomrule
\end{longtable}
\endgroup

\clearpage

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

Process-model and empirical-plan checks include:

```bash
uv run pytest -q tests/test_process_models.py tests/test_process_mining.py tests/test_empirical_taskset_manifest.py
uv run pytest -q tests/test_empirical_contracts.py tests/test_contract_capabilities.py tests/test_jurisdiction_profiles.py
```

Native Mojo/MAX checks are external gates unless the local Modular/Pixi
toolchain is available:

```bash
pixi run mojo-format-check
pixi run mojo-test
pixi run mojo-build
```

\clearpage

## Version Conventions

The package uses several independent version axes:

| Version axis | What it identifies | Current status |
| --- | --- | --- |
| Software release | The installable FOI-O Python package and its release metadata | v0.8.1 is the latest published release; no v0.9.0 or v2.0.0 release exists |
| Extraction/review contract | The rules, capabilities, evidence thresholds, and approval gates for preparing and reviewing records | A separate research-contract milestone, not a software release |
| Ontology/profile compatibility | The jurisdiction-neutral core, country profiles, and subdivision profiles and their compatible ranges | NZ is the implemented package; Australian Commonwealth and NSW remain provisional pilots |
| Source and legal materials | Archive snapshots, statutory versions, mappings, and provider-owned source packs | Each carries its own source date, hash, rights, and applicability record |

Examples and readiness files may use names such as `v0.9.0` for a planned
release package or checklist. Those names are planning identifiers only and do
not assert that the corresponding software release or dataset has been
published.

\clearpage

## S4. Ontology and Standards Alignment

FOI-O NZ uses the canonical namespace
\path{https://w3id.org/foio-nz/ontology#}. The semantic layer aligns with:

- PROV-O for events, evidence, provider runs, review tasks, and derivation;
- SKOS for controlled vocabularies;
- DCAT for dataset and catalogue metadata;
- ODRL for publication and reuse constraints;
- legal-document identifiers for source-versioned statute and guidance
  references.

Semantic alignment is documented in `docs/22-semantic-alignment.md`.

## S4A. Data Provenance and Transformation

The repository treats provenance as part of the data, not as an afterthought.
The normal flow is:

1. **Source record.** A public FYI/Alaveteli-compatible manifest or an
   archive-preserved record is identified by its request or record key. The
   source URL or archive identifier, capture time, content hash, attachment
   references, and recorded rights restrictions are retained where available.
2. **Evidence-preserving normalisation.** `foi-o-nz normalise-manifest` reads
   JSON or JSONL input and writes request profiles and event records. Observed
   labels, timestamps, message text references, and attachment references are
   kept separate from normalised state names. The mapping files under
   `mappings/` define the state conversions; they do not overwrite the source
   value.
3. **Candidate derivation.** Deterministic extraction and reporting helpers
   create candidate events, deadline annotations, RDF exports, and aggregate
   indicators. Candidate records retain evidence references, assertion status,
   generator metadata, and the profile, model, and transformation versions.
4. **Validation and review.** JSON Schema, Pydantic, SHACL, quality gates, and
   tests check structure, evidence, provenance, and safety boundaries. A
   candidate remains a candidate until an authorised reviewer records a separate
   certification or promotion decision.

The principal implementation and evidence locations are:

| Stage | Repository location | Provenance evidence |
| --- | --- | --- |
| Capture and archive inputs | `fyi-cli`, `fyi-archive`, `data/raw/` | manifests, content hashes, capture metadata, rights records |
| Normalisation and mapping | `src/foi_o_nz/`, `mappings/` | source keys, mapping identifiers, transformation version, evidence references |
| Derived examples and reports | `examples/`, `data/processed/` | generator metadata, input hashes, deterministic commands, warning fields |
| Semantic and structural checks | `ontology/`, `shacl/`, `schemas/`, `tests/` | validation reports, schema versions, test results |
| Publication assets | `examples/generated-asset-manifest.foi-o-publication.json`, `scripts/build_submission_latex.py` | source inputs, commands, output hashes, captions, and package inventory |

For a reproducible local run, start with the commands in `README.md` under
“Normalise FYI manifest records” and “Normalise a batch”, then run
`uv run pytest -q`. The commands operate on pinned or example inputs and do not
silently fetch or republish private source material. Source contents, legal
rights, and external provider verification remain separate gates from the
repo-local transformation checks.

\clearpage

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

The extraction-contract work additionally requires immutable source/profile/model
pins, rights-reviewed heldout data, independent annotation and adjudication,
empirical acceptance metrics, and explicit human promotion. The archive, Australian Commonwealth,
and NSW adapters remain candidate pilots until those conditions are evidenced.

## S5A. Cross-Repository Programme Handoffs

| Repository or dataset | Handoff to FOI-O |
| --- | --- |
| `fyi-cli` | Capture and delta inputs from FYI/Alaveteli-compatible sources. |
| `fyi-archive` | Archive fidelity, manifests, provenance, and dataset packaging. |
| `edithatogo/fyi-archive-nz` on Hugging Face | Versioned public dataset distribution boundary. |
| `foi-process` | Document-evidence and OCR integration spine. |
| `nlp-policy-nz` | Review-bounded adapter extraction and empirical evaluation. |
| `legislation` | Versioned statutory source packs. |
| `rulespec-nz` | Deterministic New Zealand rule specifications. |
| `rac-conformance` | Cross-repository programme conformance evidence. |

Alaveteli is used as a source of public metadata and workflow intelligence. It
is not represented as an FOI-O implementation repository.

\clearpage

## S6. Generated Asset Plan

The final publication package should include generated diagrams, tables, plots,
and graph/network files. The current source package includes a text-renderable
architecture diagram in the manuscript and a committed Mermaid state-machine
example at `examples/state-machine.mmd`.

\begingroup
\scriptsize
\setlength{\tabcolsep}{2pt}
\begin{longtable}{>{\raggedright\arraybackslash}p{0.17\linewidth}>{\raggedright\arraybackslash}p{0.27\linewidth}>{\raggedright\arraybackslash}p{0.20\linewidth}>{\raggedright\arraybackslash}p{0.18\linewidth}}
\caption{Generated asset plan for the FOI-O NZ supplement. Abbreviations: FOI-O, Freedom of Information Ontology; NZ, New Zealand; BPMN, Business Process Model and Notation; PNML, Petri Net Markup Language; XES, eXtensible Event Stream; OCEL, Object-Centric Event Log.}\\
\toprule
Asset & Source input & Output target & Status \\
\midrule
\endfirsthead
\caption[]{Generated asset plan for the FOI-O NZ supplement continued.}\\
\toprule
Asset & Source input & Output target & Status \\
\midrule
\endhead
Architecture flow diagram & \path{docs/27-submission-manuscript.md} & Manuscript figure & Included as Mermaid source; static rendering pending final journal format. \\
State-machine diagram & \path{examples/state-machine.mmd} & Supplement figure & Source committed; static rendering pending final journal format. \\
BPMN process model & \path{process_models/foi-o-nz-core.bpmn} & Supplement process-model artefact & Committed as review/interchange source. \\
PNML Petri net & \path{process_models/foi-o-nz-core.pnml} & Supplement process-model artefact & Committed as review/interchange source. \\
Generated state-machine exports & \path{process_models/foi-o-nz-state-machine.*} & Supplement canonical process-model artefacts & Generated from the canonical state machine. \\
Process-mining XES fixture & \path{examples/process-mining.fixture.xes} & Supplement interchange artefact & Fixture-only; not live corpus validation. \\
Process-mining OCEL-style fixture & \path{examples/process-mining.fixture.ocel.json} & Supplement interchange artefact & Fixture-only; not live corpus validation. \\
Process-mining conformance report & \path{examples/process-mining-conformance.fixture.json} & Supplement conformance artefact & Fixture-only release-path check. \\
Empirical task-set manifest & \path{examples/empirical-taskset-manifest.nz-first.json} & Supplement empirical-plan artefact & Planned annotation tasks; not a gold standard. \\
Artefact inventory table & Repository file layout & Supplement table & Included. \\
Validation evidence table & \path{docs/19-release-readiness-evidence.md} & Manuscript table & Included. \\
Cosmograph node data & Ontology, schema, example, and validation relationships & Supplement graph data & Committed at \path{examples/graph-export.foi-o-evidence-network.json}; publication rendering remains journal-dependent. \\
Static graph fallback & Cosmograph node/edge data & Supplement figure & Committed as \path{docs/assets/foi-o-evidence-network.mmd}; static rendering remains journal-dependent. \\
Generated asset manifest & Diagrams, tables, graph data, captions, text alternatives, source inputs, commands, and provenance & Supplement asset index & Committed at \path{examples/generated-asset-manifest.foi-o-publication.json}. \\
\bottomrule
\end{longtable}
\endgroup

Every final asset must have a caption, alt text or textual equivalent, source
input, generation command, provenance entry, and intended manuscript/supplement
location.

\clearpage

## S7. arXiv Source-Package Readiness

The arXiv source-package workflow is documented in
\path{docs/30-arxiv-readiness.md} and represented by
\path{examples/arxiv-readiness.manuscript-planned.json}.

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

\clearpage

## S8. External Gates

The following items remain outside repo-local automation:

- live FYI/archive pulls;
- publication of future, not-yet-deposited release versions;
- Hugging Face, Zenodo, OSF, arXiv, or journal upload;
- final author list, affiliations, funding, conflicts, acknowledgements, and
  cover letter;
- external peer review and editorial acceptance;
- official government, Ombudsman, or PSC endorsement.

\clearpage

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

FOI-O v0.8.1 is preserved at
\url{https://doi.org/10.5281/zenodo.21360138}; its concept DOI is
\url{https://doi.org/10.5281/zenodo.21360137}. These identifiers establish
software preservation and citation, not manuscript acceptance or legal
validation.
