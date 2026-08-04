# FOI-O NZ semantic-core release candidate review

Status: integrity, deterministic-archive, and rights/public-scope reviews pass;
integration, release, and publication remain unauthorized.

## Exact candidate

- Target commit:
  `04ed03c52761b4a83579e8721aeef20ce2d9282e`
- Manifest canonical self-pin:
  `d1e14b94aa5e998120d0361c22dda24bc91b94dc797773050452b19c73b8553a`
- Serialized manifest SHA-256:
  `19b285d70f6d61a123602d7e1fa284b17d16f40a26be0cbd1c583025f37b8e37`
- Destination-neutral archive SHA-256:
  `86778bae632e12c6483531f13b396817d2e77d7cb1cc4fd4f51267e2e3ea66e1`
- Archive receipt SHA-256:
  `c87282d4234e45cfd3da2ea3026854f9929066df1bd66248fc1ff6f4c32e1359`
- Files: 12, exact allowlist, sorted and unique
- Total source bytes: 24,145
- Archive: 13 members and 8,209 bytes
- Publication authorized: false
- Release authorized: false
- Scope approval SHA-256:
  `6e2a10176bf8daa4b853d18911ab7fcd665228a53f214ce6aee109a760156e59`

The candidate is precisely an **FOI-O NZ semantic core**, not a global
jurisdiction-neutral ontology, source dataset, empirical evidence bundle, or
installable Python package. It contains the citation record, split-licence
notices, an artifact-specific citation and scope notice, one JSON-LD context,
the NZ seed ontology, its SHACL shapes, and four SKOS vocabularies. It excludes
broad code and schemas, mappings, examples,
Conductor records, authentic source content, archive material, credentials,
restricted evidence, empirical records, training data, and legal conclusions.

## Integrity and reproducibility review — pass

The manifest validator reproduced the exact file set from the target Git tree,
verified each Git blob ID, SHA-256, size, licence assignment, count, total size,
ordering, and canonical self-pin. Negative tests reject path traversal, missing
allowlisted files, extra members, hash changes, target-commit drift, repository
or exclusion-policy drift, noncanonical gzip/tar metadata, licence drift, and
authorization flags that do not remain false.

The archive builder writes fixed ownership, mode, order, path, and timestamp
metadata. Rebuilding the same candidate produces the same gzip/tar SHA-256. The
archive contains `RELEASE-MANIFEST.json` and exactly the 12 allowlisted files.
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
- CC BY 4.0: `LICENSE-CONTENT.md`, `LICENSE.md`,
  `CITATION-SEMANTIC-CORE.cff`, `SEMANTIC-CORE-SCOPE.md`, the generated
  `RELEASE-MANIFEST.json`, the ontology, and SKOS vocabularies.

Historical ontology and vocabulary bytes remain unchanged because earlier
analyses pin them exactly. Their disposition is recorded by the included
licence map and manifest rather than by rewriting those RDF files. This is a
rights-engineering and public-scope review, not legal certification.

## Repository validation — pass with one recorded baseline exception

- `uv run pytest -q`: 1,243 passed, 2 skipped;
- `uv run ruff check src tests scripts`: passed;
- `uv run ruff format --check src tests scripts`: 387 files formatted;
- `uv run ty check src tests scripts`: passed;
- `uv run python scripts/validate_examples.py`: passed;
- `uv run python scripts/validate_workflows.py`: passed;
- candidate manifest and archive validation: passed.

The full suite drove two repository-owned remediations: generated inventory
counts now include the two release schemas and the new test module; a historical
Homebrew executable pin remains immutable but clean environments now verify its
fail-closed execution state when that exact version is absent.

Full Conductor validation passes. Seven tracks whose `origin/main` scaffolds
referenced absent evidence ledgers now contain canonical initialization entries
that explicitly infer no historical event or external-gate satisfaction. One
pre-existing legacy track remains a warning because it has evidence without an
`evidence_schema` opt-in; it is not part of this release candidate.

The first independent review found receipt/commit, canonical-archive, licensing,
citation-scope, and Conductor-baseline defects. All were remediated in
`1993b54db7805fc0c2ebde5a7801f9360d923350` with positive and negative tests.
The branch then incorporated `origin/main` commit
`4d5126d70eec608a0ff1ed9226defedaa25e8202` without rebasing and regenerated
the candidate against the reconciled functional head
`04ed03c52761b4a83579e8721aeef20ce2d9282e`. The exact candidate requires
fresh independent review.

## Remaining gates

The repository allows squash merges only. Therefore this target commit is the
reviewable integration candidate, but it cannot be the final publication
target: a squash merge creates a new `main` commit. After an authorized merge,
the manifest, archive, receipt, and review must be regenerated against that
exact merged commit before any tag, release, deposit, or upload is authorized.

The next gate is exact branch integration authorization. Destination-specific
publication remains a second, separate gate. See
`integration-and-publication-gates.md`.
