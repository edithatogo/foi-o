# arXiv Readiness Workflow

This document defines the repo-local preflight workflow for an arXiv source
package derived from the journal submission manuscript and supplement. It is a
packaging-readiness workflow only. It does not perform arXiv upload, select a
category, certify authorship, or approve public release.

## Requirements Snapshot

The journal submission track must refresh this snapshot before producing an
upload package.

- arXiv accepts TeX/LaTeX source packages as `.tar` or `.zip` archives.
- arXiv compiles submissions from the root of the uploaded directory, even when
  the top-level file is in a subdirectory.
- arXiv currently supports TeX Live 2025 as the default and TeX Live 2023 as an
  alternative.
- Human approval is required for category choice, author metadata, declarations,
  and live upload.

## Tool Decision

Use `arxiv-latex-cleaner` as the default sanitizer. It directly addresses the
main repo risk for a public arXiv source upload: removing comments, unused files,
and avoidable image bloat from a generated LaTeX project.

Add other tools only when they cover a separate failure mode:

- `latexmk` with TeX Live 2025 is required to prove that the generated source and
  cleaned package compile against the current arXiv default toolchain.
- `arxiv-collector` is conditional. Use it when the manuscript uses bibliography
  or package dependencies that need explicit collection for upload.
- `latexpand` is conditional. Use it when the package target benefits from a
  single expanded TeX file or when include flattening simplifies review.
- `ALC-NG` is optional. Use it as a stricter second-pass sanitizer only when it
  preserves the compiled PDF and does not remove required assets.
- `gitleaks` or `trufflehog` plus `exiftool`, `qpdf`, and `pdfinfo` are package
  hygiene checks for secrets, local paths, PDF metadata, embedded files, and font
  issues.

## Readiness Contract

`schemas/json/arxiv-readiness.schema.json` defines the machine-readable
readiness report. Each report records:

- the arXiv requirements snapshot and retrieval sources;
- the selected tool pipeline and which steps are required, conditional, or
  optional;
- command-level checks and expected outputs;
- package-level checks for rebuildability, root-relative paths, source
  disclosure, and metadata;
- human-only gates that must remain outside autonomous execution.

The planned baseline report is
`examples/arxiv-readiness.manuscript-planned.json`.

## Final Gate

A package may be marked repo-locally ready only when:

- the manuscript has a generated LaTeX source package;
- the source builds under TeX Live 2025 or records unavailable tooling as a
  bounded external gate;
- the default `arxiv-latex-cleaner` package rebuilds;
- dependency collection or flattening has been applied where needed;
- source, metadata, and secret scans pass;
- the human approval gates remain explicit and unresolved until the user
  approves submission.
