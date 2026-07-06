# Submission References

This directory holds the CSL JSON seed used by the LaTeX submission pipeline.
The builder copies this file into each generated LaTeX source tree, validates it
with SourceRight when the local ignored checkout is available, and emits:

- `references.vancouver.md` for human review;
- `main.bbl` for arXiv-compatible source packaging;
- `sourceright-reference-report.json` for reference-integrity audit evidence.

The current manuscript source still has to use these records through numbered
citations before the arXiv readiness gate can pass.
