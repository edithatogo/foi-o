# Analysis lineage and reproducibility policy

All future empirical and reliability analyses must be append-only, hash-pinned,
and reproducible from their recorded parents. Existing reports remain immutable;
schema or implementation improvements produce a new version rather than
rewriting an earlier artifact.

Each analysis run must record:

- exact input artifact paths, content SHA-256 values, source-manifest pins, and
  parent transformation IDs;
- repository revision, relevant script/module SHA-256 values, dependency lock
  or environment identifier, and command arguments;
- schema, codebook, protocol, sampling seed, PRNG/library version, duplicate
  rule, exclusions, and authorization references;
- output artifact hashes, counts, denominators, missingness, and explicit
  boundary flags;
- whether the result is candidate, descriptive, frozen, gold, or promoted;
- a redacted validation digest without emitting restricted source text to logs.

Transformation stages must be one-way and named: capture, validation,
classification, text extraction, frame creation, sampling, annotation,
adjudication, reliability, and maturity decision. A later stage may reference
an earlier stage only through its hash-pinned artifact; it may not mutate or
silently replace it.

Shared computation belongs in common versioned libraries. Jurisdiction wrappers
may supply only pins, schemas, role prefixes, and population parameters. A
compatibility test must prove that refactoring a prior report generator does not
change the prior artifact bytes unless a new schema version is intentionally
declared.

The Conductor `evidence.jsonl` ledger is append-only and records every material
transition. Git commits and notes provide implementation provenance; they do not
replace artifact hashes or human authorization. No remote publication, push,
pull request, merge, release, or dataset transfer is implied by local
reproducibility.
