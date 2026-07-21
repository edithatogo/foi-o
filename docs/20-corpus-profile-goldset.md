# Corpus Profile and Goldset Workflow

This workflow is fixture-first. Live FYI archive, Hugging Face dataset, WARC, or registry access is an external gate unless an operator supplies a source snapshot and records its provenance.

## Fixture Corpus Profile

```bash
uv run foi-o-nz normalise-manifest \
  --input data/smoke/fyi-manifest.jsonl \
  --requests-output data/smoke/requests.jsonl \
  --events-output data/smoke/events.jsonl \
  --run-manifest-output data/smoke/run-manifest.json
```

Request profiles preserve:

- raw `source_state`;
- mapped `normalised_state`;
- `state_mapping` method, confidence, notes, and evidence ids;
- `source_provenance` with input path, source record id, raw state field/value, mapping basis, and evidence id.

If a live source URL is configured but the local manifest is missing, normalisation fails closed before writing outputs and reports the live source as an external gate.

## Deterministic 100-Request Sample

```bash
uv run foi-o-nz sample-goldset \
  --input data/processed/requests.jsonl \
  --output data/processed/goldset.requests.jsonl \
  --manifest-output data/processed/goldset.requests.manifest.json \
  --kind request \
  --limit 100 \
  --per-stratum 100 \
  --seed foi-o-nz-goldset-v0.1
```

The committed tests use a smaller fixture-equivalent and verify that the same seed selects the same records.

## Request State-Mapping Tasks

```bash
uv run foi-o-nz build-goldset \
  --requests-jsonl data/processed/requests.jsonl \
  --events-jsonl data/processed/events.jsonl \
  --output data/processed/goldset.request-tasks.jsonl \
  --summary-output data/processed/goldset.request-tasks.summary.json
```

These tasks are annotation and evaluation aids only. They include source state, normalised state, mapping confidence, source provenance, and event hints so reviewers can judge whether the mapping is supported. They do not certify OIA outcomes.

## Empirical Task-Set Manifest

The planned NZ reference-profile empirical work is recorded in
`examples/empirical-taskset-manifest.nz-first.json` and validated against
`schemas/json/empirical-taskset-manifest.schema.json`.

The manifest makes the current evidence boundary explicit:

- the 100-request state-mapping set is planned, not completed;
- timeline, outcome, legal-issue, and attachment tasks are smaller planned
  annotation sets;
- every task set has the claim boundary
  `annotation_task_until_human_reviewed`;
- the manifest-level boundary is `annotation_tasks_not_gold_standard`.

Do not describe these task sets as a gold standard until source snapshots,
reviewer instructions, human review, adjudication, and any agreement metrics
are recorded.

## Repo-Local Validation

```bash
uv run pytest -q tests/test_normalise.py tests/test_request_profile_jsonld.py tests/test_review_advice_graph_attestation_gold_annotation.py
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
```

Expected repo-local result: all selected tests pass, example validation prints `examples ok`, and repository validation prints `repository validation ok`.
