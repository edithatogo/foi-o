# Journal and Preprint Target Requirements

## Target Decision

The primary near-term target is an arXiv preprint plus later submission to a
journal that accepts methods, ontology engineering, research software, semantic
web, legal informatics, or digital-government outputs.

This staged route is appropriate because the current repository can provide
repo-local evidence for schema contracts, ontology alignment, tests, examples,
and reproducibility commands, while live journal upload, author declarations,
category choice, and external editorial decisions require human approval.

## Candidate Venues

| Venue | Fit | Main risk | Current decision |
| --- | --- | --- | --- |
| arXiv | Fast public dissemination of a methods/software preprint with source package checks. | Category choice, author approval, and source-package hygiene remain human gates. | Primary preprint route. |
| Journal of Biomedical Semantics | Ontology and semantic-modelling audience. | May require a stronger domain-specific evaluation and formal reporting checklist. | Candidate journal after protocol/results tracks mature. |
| Semantic Web Journal | Strong semantic-web and ontology-engineering audience. | Requires substantial semantic-web contribution and possibly richer ontology evaluation. | Candidate fallback. |
| Journal of Open Source Software | Research software publication route. | Requires installable software paper framing and reviewer checklist. | Candidate if software contribution is prioritised. |
| Government Information Quarterly | Digital-government and public-sector information governance audience. | Needs stronger empirical and policy-analysis framing. | Candidate after corpus/results expansion. |

## Current Requirements Snapshot

The current source-package readiness workflow is documented in
`docs/30-arxiv-readiness.md` and validated through
`examples/arxiv-readiness.manuscript-planned.json`.

The submission package must include:

- a manuscript with title, abstract, keywords, introduction, methods, results,
  discussion, limitations, conclusion, data/code availability, funding/conflict
  placeholders, and references;
- a supplement with schema, ontology, SHACL, vocabulary, example, validation,
  and generated-asset inventories;
- explicit non-legal-advice and non-official-publication boundaries;
- repo-local validation commands and outputs;
- a source-package preflight plan using `arxiv-latex-cleaner` as the default
  sanitizer, TeX Live 2025/`latexmk` compile proof, conditional
  `arxiv-collector` or `latexpand`, optional ALC-NG, and package hygiene scans;
- human gates for author list, affiliations, funding, conflicts, category
  selection, cover letter where applicable, and final upload approval.

## External Gates

The following steps are not completed by repository automation:

- arXiv category selection and upload;
- journal account upload;
- final author list, affiliations, acknowledgements, funding, conflicts, and
  data-use declarations;
- journal-specific production checks;
- peer review, acceptance, DOI registration, or indexing.
