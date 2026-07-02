# Local/MAX Inference Boundaries

FOI-O NZ supports bounded local extraction experiments without changing the
human-certification boundary.

## Candidate-only prompt packs

Use `prepare-local-extraction` to create local JSONL request packs:

```bash
uv run foi-o-nz prepare-local-extraction \
  --input data/processed/source-records.jsonl \
  --output data/processed/local-extraction-requests.jsonl \
  --text-field body \
  --provider deterministic
```

For a local MAX/OpenAI-compatible endpoint, set `--provider max` and optionally
provide `--model` and `--endpoint`. Provider selection records provenance but
does not contact the endpoint while preparing request packs.

## Safety contract

Each request pack records:

- `generated_output_included: false`;
- `review_required: true`;
- `legal_effect: none`;
- `machine_certification_allowed: false`;
- input text SHA-256 and bounded prompt text;
- provider provenance and allowed output status values.

Generated model outputs are not release/refusal/redaction/charging/extension
certifications. They must be validated as candidate events, routed for human
review, and reduced to safe fixtures before committing them to the repository.

## External gates

Running a live MAX endpoint, downloading local models, or using GPU/accelerator
tooling is an external gate. Repo-local validation covers prompt-pack creation,
provider provenance, deterministic fallback, and rejection of unsafe certified
machine outputs.
