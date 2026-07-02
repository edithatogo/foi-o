# Product Definition

## Initial Concept

FOI-O NZ is an agent-facing process model, ontology, validation stack, and analytical workbench for New Zealand Official Information Act administration.

## Mission

FOI-O NZ defines a machine-readable, auditable model of New Zealand OIA process data for use by humans, software systems, and bounded AI agents. It sits beside the FYI ecosystem as the semantic and process layer for request profiles, core process events, validation contracts, analytics, evaluation, and future MCP resources/tools.

## Users

- Maintainers of FOI-O NZ and related FYI tooling.
- Researchers and data engineers working with public OIA process records.
- Agent/runtime developers who need bounded, auditable tools for state mapping, validation, retrieval, and quality checks.
- Human reviewers who certify release, refusal, redaction, extension, transfer, charging, and complaint outcomes.

## Product Scope

FOI-O NZ owns the process/event ontology, JSON Schemas, SKOS vocabularies, SHACL shapes, mappings, extraction and evaluation prompts, deterministic validation utilities, analytics, review queues, agent contracts, and small committed examples. It depends on adjacent projects for capture, archive orchestration, publication, and corpus hosting.

The project is not an autonomous FOI decision system. Its purpose is to help agents and software systems draft, validate, route, summarise, and flag process evidence while preserving hard human certification boundaries.

## Current Capabilities

- Strict JSON Schema and Pydantic models for request profiles, process events, agent actions, review tasks, metrics, manifests, and related records.
- FYI/Alaveteli manifest normalisation into request and event streams.
- State mapping, transition auditing, quality gates, deadline calculations, and reporting summaries.
- RDF/JSON-LD export, ontology seed, SKOS vocabularies, and SHACL validation.
- Deterministic text chunking, lexical/vector-style retrieval, redaction candidate generation, risk triage, ledgers, dataset metadata, reproducibility manifests, and agent context packs.
- Experimental Mojo/MAX kernels for deterministic state, clock, text, retrieval, guardrail, hash, redaction, transition, and epistemic helpers, with Python fallback contracts.
- Experimental FastMCP resources/tools for bounded state mapping, validation, and quality checks.

## Product Boundaries

Agents may map observed states, create candidate events from public manifests, calculate indicative clocks with warnings, draft search plans or correspondence, and prepare review materials.

Agents must not certify access decisions, withholding grounds, public-interest balancing, redactions, releases, charges, statutory notices, transfers, extensions, or complaint/review outcomes.

## Success Criteria

- Every public contract is documented, schema-backed, and covered by examples or tests.
- Deterministic fallback behavior remains available when optional Mojo/MAX, analytics, RDF, MCP, or vector dependencies are absent.
- Release-readiness claims match repo-local evidence.
- Human certification boundaries are visible in schemas, prompts, docs, tests, agent policies, and generated artifacts.
- Validation and reproducibility commands can be rerun by maintainers without relying on hidden state.
