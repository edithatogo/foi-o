# ADR 0004: Require human certification for decision-like events

## Status

Proposed

## Context

AI may support OIA teams by managing process and drafting artefacts, but access/refusal/redaction/charging/extension/review outcomes are legal-administrative acts.

## Decision

Schemas and SHACL shapes should require human certification metadata for decision-like events before they can be treated as final.

## Consequences

The system remains useful for process automation while preserving human accountability.
