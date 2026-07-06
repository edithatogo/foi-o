# FOI-O NZ validation coverage summary

This summary records the repo-local validation surfaces that support the
NZ-first ontology maturation package. It is a publication-source table and a
lightweight fallback for a later rendered plot.

| Validation surface | Command or evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Example/schema validation | `uv run python scripts/validate_examples.py` | JSON examples conform to committed schemas, including generated asset manifests. | Live source correctness or external publication acceptance. |
| Repository validation | `uv run foi-o-nz validate-repo` | Repo-local semantic, schema, mapping, and documentation checks pass. | Journal, arXiv, registry, or legal approval. |
| Schema drift | `uv run foi-o-nz schema-drift` | Generated and committed schema surfaces remain compatible enough to return `ok: true`. | Absence of warning-level metadata differences. |
| Maturation tests | `uv run pytest -q tests/test_ontology_maturation_plan.py` | Protocol sections, claim boundaries, path references, asset manifest, and graph data remain consistent. | Human-reviewed gold-standard completion. |
| Semantic tests | `uv run pytest -q tests/test_semantic_alignment.py tests/test_rdf_export.py tests/test_shacl_safety_profiles.py` | RDF, JSON-LD, SKOS, SHACL, and safety-profile surfaces remain aligned. | Full formal legal ontology completeness. |
| Publication tests | `uv run pytest -q tests/test_methods_paper.py tests/test_publication_quality_panel.py tests/test_submission_package.py` | Publication documents and panel/checklist fixtures remain valid and bounded. | Peer review, journal fit, or final submission approval. |
| Maturation summary | `uv run foi-o-nz maturation-summary --output examples/maturation-summary.ontology-maturation.json` | Inventory counts, maturation documents, assets, validation commands, and external gates can be regenerated from the repo tree. | Human-reviewed evaluation outcomes or publication approval. |
| Process-model conformance | `uv run foi-o-nz process-model-conformance --output examples/process-model-conformance.ontology-maturation.json` | Hand-authored BPMN/PNML workflow models preserve human certification and are explicitly compared with generated canonical state-machine exports. | Full process-mining validation or legal workflow execution. |
| Full Python suite | `uv run pytest -q` | All committed Python tests pass. | Native Mojo release certification or live optional services. |
| Ruff checks | `uv run ruff check src tests scripts`; `uv run ruff format --check src tests scripts` | Python code style and formatting are clean. | Scientific or legal adequacy. |
| Native Mojo/Pixi checks | `pixi run mojo-format-check`; `pixi run mojo-test`; `pixi run mojo-build` | Native kernels format, test, and build where the toolchain is available. | MAX model quality or live inference performance. |

## External Gates

The coverage summary is repo-local evidence. It does not complete live
FYI/archive pulls, live legal-source refresh, registry upload, journal
submission, arXiv upload, official reporting validation, or human legal/author
approval.
