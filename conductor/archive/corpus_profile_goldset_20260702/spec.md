# Specification: Corpus profile and 100-request goldset

## Objective

Implement live/fixture-backed FYI archive intake, source-state preservation, request JSON-LD profile completion, and a reproducible 100-request goldset workflow.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/12
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Support a documented corpus-profile workflow that can run against committed fixtures and, when configured, live FYI archive manifest inputs.
- Preserve original FYI/Alaveteli state labels alongside normalised FOI-O NZ states.
- Complete request-level JSON-LD profile coverage for the current request-profile schema.
- Provide deterministic goldset sampling for 100 requests with annotation-task exports and reproducible provenance.
- Keep live external source availability separate from repo-local fixture proof.

## Acceptance Criteria

- Fixture corpus profile commands validate request profiles, events, JSON-LD context, and goldset outputs.
- A maintainer can rerun a 100-request sample workflow or a smaller fixture-mode equivalent without hidden state.
- Source state, normalised state, confidence, evidence, and provenance are present in generated review data.
- Live FYI/archive/Hugging Face access is documented as an external gate when unavailable.
