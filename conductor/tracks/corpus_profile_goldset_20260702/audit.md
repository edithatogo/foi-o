# Corpus Intake and Request Profile Audit

## Current Repo-Local Proof

- `src/foi_o_nz/io.py::read_json_records` accepts JSONL, JSON arrays, JSON objects with a `records` array, and single JSON objects.
- `src/foi_o_nz/normalise.py::build_request_profile` preserves the FYI/Alaveteli source state in `source_state` and stores the mapped FOI-O state plus rule confidence in `state_mapping`.
- `normalise-manifest` writes request profiles, core events, optional Parquet outputs, and an optional run manifest.
- `sample-goldset` deterministically samples JSONL records with a seed, limit, and per-stratum cap.
- `build-goldset` builds bounded review tasks from chunk/risk records.

## Gaps To Close In Phase 1

- Request profiles do not yet expose structured source provenance naming the input file, record identifier, raw state field, and mapping basis.
- Fixture tests cover JSONL input, but not JSON array or `{"records": [...]}` manifest variants.
- There is no fail-closed live-source configuration test for missing FYI/archive inputs.
- `examples/request-record.jsonld` is stale: it maps FYI `successful` to `decision_communicated`, while the current state machine maps it to `ReleasedInFull`.
- `contexts/foi-o-nz.context.jsonld` is mostly event-oriented and does not yet describe request-profile provenance terms.

## Repo-Local Versus Live-Source Boundary

- Repo-local proof should use committed fixtures, temp-file manifests, schema validation, and deterministic goldset seeds.
- Live FYI archive, Hugging Face dataset, or WARC fetch availability is an external gate unless credentials, network source, and source snapshot are explicitly configured.
- Live-source failures must not prevent fixture-mode normalisation, schema validation, or deterministic goldset sampling.

## Next Tests

- Add normalisation tests for JSON array and `records` wrapper inputs.
- Add a request-profile provenance test that expects source file, source record id, raw state field, mapping method, mapping confidence, and evidence id.
- Add a fixture-mode live-source failure test that proves missing configured live manifests fail with a bounded error before any output is written.
