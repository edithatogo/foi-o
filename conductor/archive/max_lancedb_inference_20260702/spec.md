# Specification: MAX and LanceDB bounded inference

## Objective

Add bounded MAX/local extraction and embedding integration plus LanceDB semantic retrieval, with deterministic fallback and no legal-decision behavior.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/17
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Provide a bounded inference provider interface for extraction/embedding experiments.
- Preserve deterministic feature-hash embeddings and rule extractors as fallback contracts.
- Add LanceDB semantic retrieval integration behind optional dependency gates.
- Ensure model outputs are candidate/preparatory only and never certified legal outcomes.

## Acceptance Criteria

- Tests cover provider selection, deterministic fallback, optional dependency absence, and unsafe output rejection.
- Fixture-mode retrieval works without model downloads, keys, GPUs, or MAX runtime.
- Live/model-backed commands document required external gates and do not write generated payloads to Git by default.
- Agent packs record model/fallback provenance and human-review requirements.
