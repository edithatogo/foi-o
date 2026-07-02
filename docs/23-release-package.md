# Publication Release Package

This note defines the repo-local release package for FOI-O NZ. It prepares
publication evidence without performing external registry publication.

## Package scope

The release package covers code, schemas, ontology, SHACL/SKOS vocabularies,
small examples, documentation, Conductor evidence, and generated metadata
fixtures in this repository.

It does not republish source FYI/archive payloads. Source request/archive
content remains subject to its original rights and platform terms.

## Machine-readable checklist

The release checklist fixture is:

```bash
examples/release-checklist.v0.9.0.json
```

Regenerate it with:

```bash
uv run foi-o-nz release-checklist --output examples/release-checklist.v0.9.0.json --release-version 0.9.0
```

Validate it with:

```bash
uv run pytest -q tests/test_release_package.py
uv run python scripts/validate_examples.py
```

## Repository release metadata

The repository-release metadata fixture is:

```bash
examples/repository-release-metadata.v0.9.0.json
```

Regenerate it with:

```bash
uv run foi-o-nz repository-release-metadata \
  docs/23-release-package.md \
  examples/release-checklist.v0.9.0.json \
  examples/dataset-metadata.examples.json \
  docs/23-methods-paper.md \
  --output examples/repository-release-metadata.v0.9.0.json \
  --release-version 0.9.0 \
  --base-dir .
```

## Required repo-local validation

Before claiming repo-local release readiness, run:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
uv run python scripts/validate_examples.py
```

Available Mojo/MAX checks should also be run for native-kernel release evidence:

```bash
pixi run mojo-format-check
pixi run mojo-test
pixi run mojo-build
```

## External gates

The checklist marks these as external or manual gates:

- GitHub release publication.
- Hugging Face dataset publication.
- Zenodo or OSF deposit.
- Live FYI/archive pulls.
- Native Mojo/MAX release certification when local tooling is unavailable.

Passing repo-local checks does not complete those external gates.
