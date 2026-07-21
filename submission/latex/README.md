# FOI-O NZ LaTeX Submission Pipeline

This directory contains tracked configuration for the repository-local
submission build. Generated source trees, PDFs, logs, and upload packages are
written under `build/submission/latex/`.

## Targets

| Target | Engine | Purpose |
| --- | --- | --- |
| `arxiv` | `pdflatex` through `latexmk` | Conservative source package for arXiv-style upload checks. |
| `enhanced` | `lualatex` through `latexmk` | Local accessibility/tagged-PDF experiment with `\DocumentMetadata`. |

The arXiv target is the compatibility gate. The enhanced target is useful for
local inspection and future accessibility work, but it must not replace the
arXiv package unless it also passes the arXiv checks.

## Commands

```bash
uv run python scripts/build_submission_latex.py arxiv
uv run python scripts/build_submission_latex.py enhanced
uv run python scripts/build_submission_latex.py all --strict
```

The script records command logs, PDF metadata checks, source hygiene checks,
figure checks, citation/reference checks, hyperlink-contract checks, and cleaner
status in a JSON manifest. The hyperlink contract requires every numbered
citation (1--30), the abbreviations and glossary anchors, and every generated
table and figure anchor to have a matching navigable link in the produced TeX.
This keeps the requested navigation elements present when the TeX is converted
to PDF.
It may use `uvx --from arxiv-latex-cleaner arxiv_latex_cleaner` when the cleaner
is not on `PATH`.
For the arXiv target, the compiled supplement is added to the upload archive as
`anc/foi-o-nz-submission-supplement.pdf`. This follows arXiv's ancillary-file
pattern and keeps the main article body separate from repository inventory and
methods-support material.

Reference preparation starts from
`submission/references/references.csl.json`. When the local ignored SourceRight
checkout is available, the builder runs `sourceright validate-csl --json`,
then emits `references.vancouver.md`, `main.bbl`, and a
`sourceright-reference-report.json` audit sidecar into the generated source
tree. Live provider enrichment remains an external gate; the offline build only
proves CSL shape and package inclusion.

The enhanced target records static accessibility checks for `\DocumentMetadata`,
PDF title/author metadata, figure alt-text coverage, and generated table header
structure. These checks are local evidence for tagged-PDF experiments, not a
claim that the PDF is production-accessible.

## Policy

- No shell escape.
- No raw Mermaid in the manuscript source.
- No absolute local paths in the upload package.
- No hidden local fonts or private font dependencies.
- No unresolved citations or references.
- Vancouver-style numbered references are required for the manuscript.
- CSL references are the source of truth for generated Vancouver bibliography
  artifacts.
- TeX Live 2025 parity is recorded separately from local TeX builds.
