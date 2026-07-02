# Product Guidelines

## Voice and Content

- Use precise, evidence-oriented language.
- State capability boundaries plainly, especially when describing agent behavior.
- Prefer "candidate", "observed", "inferred", "asserted", and "certified" terminology where epistemic status matters.
- Avoid language implying legal advice, official government status, or autonomous OIA decision authority.
- Keep README, docs, schemas, examples, and release notes aligned with the actual tested implementation.

## User Experience

- Developer-facing commands should be copyable, deterministic, and non-interactive where possible.
- Error messages should identify the invalid file, schema, record, field, or boundary condition.
- Review outputs should prioritize traceable evidence, provenance, and next human action.
- Optional integrations must degrade gracefully to deterministic local behavior.

## Safety and Governance

- Preserve a hard human certification boundary in user-facing and agent-facing surfaces.
- Treat redaction, release/refusal, charging, statutory notices, and complaint outcomes as human-certified decisions.
- Record provenance, timestamps, hashes, and source context for generated artifacts where relevant.
- Keep public examples small, synthetic or safe, and suitable for committed test fixtures.

## Documentation Standards

- Document new public CLI commands, schemas, MCP tools, and generated output formats in the same change that introduces them.
- Prefer examples that can be validated by existing test or schema commands.
- Separate implemented, experimental, and planned surfaces.
- Do not let roadmap language outrun repo-local proof.

## Data and Artifact Standards

- Generated data belongs outside Git unless it is a small committed fixture, schema example, or manifest needed for tests.
- JSONL streams should be canonical, stable, and suitable for hash-based comparison.
- Any release or readiness report must cite the exact command, file, or manifest that supports the claim.
