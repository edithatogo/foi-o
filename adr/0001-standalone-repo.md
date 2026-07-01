# ADR 0001: Use a standalone repository

## Status

Proposed

## Context

`fyi-cli` owns local request-management/capture functionality. `fyi-archive` owns archive orchestration, manifests, mirror publication, and provenance. FOI-O NZ concerns process semantics, ontology, validation, agent boundaries, and evaluation.

## Decision

Create a standalone repository for FOI-O NZ.

## Consequences

Positive:

- avoids mixing capture logic with conceptual modelling;
- keeps the ontology independently citable and versioned;
- allows schema releases without archive releases;
- supports reuse by future non-FYI OIA systems.

Negative:

- introduces another repo to maintain;
- requires clear dependency/version references to `fyi-cli`, `fyi-archive`, and `fyi-archive-nz`.
