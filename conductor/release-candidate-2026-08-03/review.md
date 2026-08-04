# FOI-O NZ semantic-core release candidate review

Status: integrity, deterministic-archive, and rights/public-scope reviews pass;
integration, release, and publication remain unauthorized.

## Exact candidate

- Target commit:
  `154c64fbde0ad558f7f60159c9289a0115a2f63f`
- Manifest canonical self-pin:
  `3b8799f220dcb76bac913716ccf8cf60664c59b3770fe48f9987b3d1b20ff03f`
- Serialized manifest SHA-256:
  `550a2b5c53b8fe15ebb050ffc58b8b924c09d930b1f90c720f916291f14854f2`
- Destination-neutral archive SHA-256:
  `dcdb26f1b6c1bdc43d65627f22ce6f2ffe8d97504f76dbbb5b00d7fabdea699c`
- Archive receipt SHA-256:
  `5135b726f978ec67d99353c48eadc11160eac6e559abe50f67b7ef93456a899e`
- Files: 11, exact allowlist, sorted and unique
- Total source bytes: 23,554
- Archive: 12 members and 7,882 bytes
- Publication authorized: false
- Release authorized: false
- Scope approval SHA-256:
  `6e2a10176bf8daa4b853d18911ab7fcd665228a53f214ce6aee109a760156e59`

The candidate is precisely an **FOI-O NZ semantic core**, not a global
jurisdiction-neutral ontology, source dataset, empirical evidence bundle, or
installable Python package. It contains the citation record, split-licence
notices, one JSON-LD context, the NZ seed ontology, its SHACL shapes, and four
SKOS vocabularies. It excludes broad code and schemas, mappings, examples,
Conductor records, authentic source content, archive material, credentials,
restricted evidence, empirical records, training data, and legal conclusions.

## Integrity and reproducibility review — pass

The manifest validator reproduced the exact file set from the target Git tree,
verified each Git blob ID, SHA-256, size, licence assignment, count, total size,
ordering, and canonical self-pin. Negative tests reject path traversal, missing
allowlisted files, extra members, hash changes, licence drift, and authorization
flags that do not remain false.

The archive builder writes fixed ownership, mode, order, path, and timestamp
metadata. Rebuilding the same candidate produces the same gzip/tar SHA-256. The
archive contains `RELEASE-MANIFEST.json` and exactly the 11 allowlisted files.
Its receipt is candidate-only and independently validates archive bytes,
members, manifest identity, and authorization flags.

Canonical validation:

```text
uv run python scripts/build_release_manifest.py --repo . \
  --validate conductor/release-candidate-2026-08-03/manifest.json
release manifest validation: PASS

uv run python scripts/build_release_bundle.py --repo . \
  --manifest conductor/release-candidate-2026-08-03/manifest.json \
  --bundle conductor/release-candidate-2026-08-03/foi-o-nz-semantic-core-0.1.0.tar.gz \
  --receipt conductor/release-candidate-2026-08-03/bundle-receipt.json --validate
release bundle validation: PASS
```

## Rights and public-scope review — pass

No candidate member contains local paths, credentials, approval prose, case or
request identifiers, authentic source content, archive material, evidence pins,
or redistribution-sensitive records. Per-file licensing matches the approved
split:

- MIT: `LICENSE-CODE.md`, the JSON-LD context, and SHACL validation schema;
- CC BY 4.0: `LICENSE-CONTENT.md`, `LICENSE.md`, `CITATION.cff`, the ontology,
  and SKOS vocabularies.

Historical ontology and vocabulary bytes remain unchanged because earlier
analyses pin them exactly. Their disposition is recorded by the included
licence map and manifest rather than by rewriting those RDF files. This is a
rights-engineering and public-scope review, not legal certification.

## Repository validation — pass with one recorded baseline exception

- `uv run pytest -q`: 1,237 passed, 2 skipped;
- `uv run ruff check src tests scripts`: passed;
- `uv run ruff format --check src tests scripts`: 386 files formatted;
- `uv run ty check src tests scripts`: passed;
- `uv run python scripts/validate_examples.py`: passed;
- `uv run python scripts/validate_workflows.py`: passed;
- candidate manifest and archive validation: passed.

The full suite drove two repository-owned remediations: generated inventory
counts now include the two release schemas and the new test module; a historical
Homebrew executable pin remains immutable but clean environments now verify its
fail-closed execution state when that exact version is absent.

The bundled Conductor validator reports seven evidence links already broken on
`origin/main` because those active tracks opt into evidence ledgers but do not
contain `evidence.jsonl`. The two tracks introduced by this branch validate.
No absent unrelated ledger was reconstructed from uncommitted workspace state.

## Remaining gates

The repository allows squash merges only. Therefore this target commit is the
reviewable integration candidate, but it cannot be the final publication
target: a squash merge creates a new `main` commit. After an authorized merge,
the manifest, archive, receipt, and review must be regenerated against that
exact merged commit before any tag, release, deposit, or upload is authorized.

The next gate is exact branch integration authorization. Destination-specific
publication remains a second, separate gate. See
`integration-and-publication-gates.md`.
