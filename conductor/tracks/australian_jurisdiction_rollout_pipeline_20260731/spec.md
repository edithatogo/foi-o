# Specification: Australian jurisdiction rollout pipeline

## Problem

The Commonwealth and New South Wales pilots proved the governance model but
required too many jurisdiction-specific scripts, manually assembled approval
packets, transient replay checkpoints, and late dependency discoveries. The
remaining seven jurisdictions must retain the same evidence boundaries without
repeating that operational cost.

## Scope

Implement one reusable, fail-closed pipeline contract:

`discover → select → replay → reconcile → classify → validate → manifest → frame → sample → calibrate → annotate → evaluate → maturity packet`

The contract plans and verifies stages; it never treats planning, validation,
or a completed predecessor as authorization for a gated successor.

## Requirements

### FOIO-REQ-AU-PIPE-001 — resumable content-addressed stages

- Every stage declares exact input pins, output artifact identities, producer
  revision, transformation version, parameters, completion state, and failure
  dispositions.
- A stage can resume only when its checkpoint digest and predecessor output
  pins validate.
- Network workers expose serial/adaptive pacing, bounded retries, typed failure
  classes, and exact-URL replacement queues without population expansion.
- Durable checkpoint artifacts are produced from the first successful batch,
  not only at workflow completion.

### FOIO-REQ-AU-PIPE-002 — shared Australian empirical contracts

- A jurisdiction-neutral Australian authority registry and codebook core may
  be composed with explicit jurisdiction overlays.
- Overlay composition rejects identifier collisions, undeclared overrides,
  foreign legal assumptions, and incompatible versions.
- Metadata classification precedes full-text acquisition and preserves
  unresolved and out-of-scope records.
- Calibration must satisfy its registered gate before the full annotation
  workload can become executable.

### FOIO-REQ-AU-PIPE-003 — reproducible governance

- Every derived artifact records source pins, transformation identity and
  version, code revision, parameters, environment declaration, and canonical
  digest.
- Generated approval wording identifies exactly what a gate authorizes and
  carries forward explicit exclusions.
- Historical analyses remain verifiable against the producer and contract
  versions that assessed them.
- Markdown/Mermaid and BPMN 2.0 describe the same stage and gate topology.

## Rollout order

Dependencies are resolved before capture. Jurisdictions are grouped by capture
platform family for engineering reuse, but legal evidence, sampling,
annotation, and maturity decisions remain jurisdiction-specific. The tranche
order is finalized from the live dependency audit and recorded in the parent
track rather than inferred from platform similarity.

## Safety and authority

Repository-owned planning, schemas, validators, fixtures, documentation, and
issue synchronization may proceed autonomously. Network capture/replay, rights
approval, empirical freezing, annotation execution, profile promotion,
publication, redistribution, and external merge remain explicit gates. A
pipeline state never grants its own authority.

## Acceptance

- Positive and negative fixtures exercise stage order, pins, resume rules,
  authorization boundaries, overlay composition, and provenance replay.
- An independent validator recomputes canonical hashes without importing the
  producer implementation.
- Existing AU-CTH and AU-NSW artifacts remain reproducible and unchanged.
- Full repository schema, workflow, Conductor, and test gates pass.
