# Release Evidence and Publication Metadata Audit

Scope: Track `publication_methods_release_20260702`, Phase 1.

## Existing evidence

- `docs/19-release-readiness-evidence.md` lists repeatable repo-local validation
  commands and external gates.
- `examples/reproducibility-manifest.examples.json` records local tool and file
  evidence for selected artefacts.
- `src/foi_o_nz/dataset_metadata.py` can generate compact dataset metadata,
  Frictionless-style datapackages, Croissant-style JSON-LD, and Hugging Face
  dataset-card scaffolds.
- `examples/dataset-metadata.examples.json` validates the current
  `dataset-metadata.schema.json` contract.
- Archived Conductor tracks contain phase/final verification reports for the
  completed roadmap slices.

## Gaps

1. There is no single versioned release checklist or package manifest that
   binds repo version, validation commands, evidence files, dataset metadata,
   methods-paper source, rights notices, and external gates.
2. Release-readiness docs list commands, but tests only assert the basic command
   sequence and a few legacy paths. They do not validate a machine-readable
   checklist against the repository.
3. Dataset metadata caveats are correct but still generic. Release-package
   metadata should explicitly separate MIT-licensed code/schemas/docs from
   source FYI/archive content rights and manual registry-publication approval.
4. Publication registry claims are intentionally not implemented. The release
   package must mark Hugging Face, Zenodo/OSF, GitHub release publication, live
   source pulls, and model/native certification as external gates unless
   credentials/tooling and human approval are present.
5. The short methods paper does not yet exist, so release notes cannot cite it
   as a prepared publication artefact.

## Phase 1 recommendations

- Add a repo-local release checklist fixture under `examples/`.
- Add a JSON Schema/Pydantic model for the checklist and validate it through
  existing example validation.
- Add tests that ensure checklist evidence paths and command references are
  real, and external gates are explicitly marked.
- Add a release package note under `docs/` that cites the checklist, existing
  validation commands, metadata outputs, rights boundaries, and manual external
  gates.
