# Implementation delta v0.5

This pass extends FOI-O NZ from process modelling and evidence ledgers into a more complete, bounded agent workbench. The goal is not to add autonomous decision-making. It is to add deterministic primitives that future MCP/MAX agents can rely on before any model inference is introduced.

## Added

- `retrieval.py`: dependency-light chunk retrieval with BM25-style lexical scoring and deterministic feature-hash vector blending.
- `redaction.py`: candidate sensitive-span detection that emits hashed/masked previews only. It does not redact, withhold, or decide.
- `diff.py`: canonical JSONL stream diffs for incremental archive workflows.
- `agent_pack.py`: request-scoped context packs combining request profile, events, chunks, risks, retrieval results, redaction candidates, constraints, and provenance.
- `reproducibility.py`: local/CI reproducibility manifests with tool availability and file SHA-256 digests.
- `mojo/foi_o_nz/retrieval.mojo`: small native retrieval scoring kernels for future compiled/reranking paths.

## New CLI commands

```bash
foi-o-nz search-chunks
foi-o-nz propose-redactions
foi-o-nz diff-jsonl
foi-o-nz build-agent-pack
foi-o-nz repro-manifest
```

## New schemas

```text
schemas/json/retrieval-result.schema.json
schemas/json/redaction-candidate.schema.json
schemas/json/diff-report.schema.json
schemas/json/agent-pack.schema.json
schemas/json/reproducibility-manifest.schema.json
```

## Safety stance

The redaction candidate pipeline deliberately stores `text_sha256` and `masked_preview` rather than raw candidate text. This preserves review utility while reducing accidental leakage in downstream agent context packs.

The agent pack embeds the human-certification boundary as data so downstream runtimes can inspect and enforce it:

```text
agents may retrieve, summarise, draft, flag, and validate;
agents must not certify release, refusal, redaction, charging, transfer, extension, or review outcomes.
```

## Why this matters

These primitives move the repository toward an agent-native administrative-law workbench:

1. agents retrieve bounded process context with deterministic search;
2. candidate risks/redaction spans are explicit but non-dispositive;
3. context packs are request-scoped and provenance-bearing;
4. diffs and reproducibility manifests make incremental processing auditable;
5. Mojo kernels remain small, testable, and safe while the wider Mojo/MAX ecosystem evolves.
