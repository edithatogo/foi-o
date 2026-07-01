# Data governance

FOI-O NZ is based on public material, but public does not mean risk-free.

## Data risks

| Risk | Mitigation |
|---|---|
| Re-identification of requesters or third parties | Minimise replicated text; preserve links and hashes; redact examples where possible. |
| Amplifying personal or sensitive information | Avoid including full correspondence unless necessary; use excerpts sparingly. |
| Treating FYI.org.nz as authoritative agency data | Model FYI data as public-platform observations, not internal agency records. |
| Over-confident state mapping | Store mapping method and confidence; keep source state. |
| Applying current law to historical events | Store law/guidance version and retrieval timestamp. |
| Prompt injection in attachments/correspondence | Treat source text as untrusted data; never execute source instructions. |
| Agent decision overreach | Validate certification boundary in schemas and tests. |
| Misuse for request spam or harassment | Do not optimise for mass request generation; focus on process management and quality. |

## Data classification

Suggested categories:

- `public_source_metadata`
- `public_correspondence_text`
- `public_attachment_metadata`
- `public_attachment_content`
- `derived_metadata`
- `agent_generated_candidate`
- `human_certified_event`
- `agency_internal_only` — placeholder for future internal deployments, not populated by public FYI data.

## Takedown and correction posture

The repo should not mirror contested source records. Where examples are needed, prefer synthetic examples, short excerpts, or references to archive identifiers. If a public source changes or is removed, downstream corpora should preserve provenance and clearly indicate snapshot status.
