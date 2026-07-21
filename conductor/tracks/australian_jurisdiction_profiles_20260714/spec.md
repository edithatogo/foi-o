# Australian FOI jurisdiction profiles

## Overview

Iterate the global FOI-O model, which originated in its mature NZ reference
profile, through evidence-backed Australian profiles without weakening the
jurisdiction-neutral core or treating Australian
information-access regimes as legally interchangeable.

## Provenance and integration

This track incorporates conformance, source-triangulation, fixture-independence,
and release-evidence lessons from `edithatogo/rac-conformance`. Those lessons
are informative design provenance, not a claim that PIC is an adopted standard
or a required runtime dependency.

- Profile contracts and deterministic artifacts should be PIC-compatible where
  that creates a tested consumer boundary.
- `edithatogo/legislation` remains authoritative for pinned legal-source
  manifests; FOI-O does not duplicate source capture.
- `edithatogo/fyi-archive` remains authoritative for immutable public-example
  manifests; FOI-O stores derived candidate and review artifacts separately.
- `edithatogo/nlp-policy-nz` may produce ontology-pinned candidates but cannot
  certify legal mappings, fixtures, or outcomes.

## Rollout

1. Pilot Commonwealth and New South Wales.
2. Evaluate the profile contract and annotation reliability.
3. Add ACT, Queensland, Victoria, Western Australia, South Australia, Tasmania,
   and Northern Territory as separate jurisdiction extensions.

## Requirements

- Consume pinned, bitemporal source manifests from `edithatogo/legislation`.
- Model primary legislation, subordinate instruments, regulator guidance,
  review pathways, deadlines, fees, exemptions, public-interest tests,
  proactive release, disclosure logs, and point-in-time applicability.
- Preserve raw RightToKnow/Alaveteli states and correspondence separately from
  normalised FOI-O concepts.
- Keep jurisdiction-neutral concepts in the core and legal rules in explicit
  profiles with provenance and effective dates.
- Maintain candidate, reviewed, and certified states; machine extraction cannot
  certify legal outcomes.
- Require representative public examples and human-reviewed fixtures for every
  jurisdiction before that profile is described as validated.
- Version the profile interface, capability declarations, migration behavior,
  and rejection behavior for unknown contract versions.
- Separate observed process events, deterministic calculations, interpretive
  mappings, and human-only legal determinations in schemas and APIs.
- Emit stable identifiers, temporal parameters, source references, candidate
  fixtures, deterministic traces, value states, and epistemic status where a
  named consumer exercises those artifacts.
- Resolve source assertions deterministically from machine-readable primary and
  official evidence, routing blocked, conflicting, stale, rights-uncertain, or
  incomplete cases to a small human exception queue.
- Require independent fixture promotion: extraction or implementation agents
  may propose candidates but cannot certify their own outputs.
- Exercise the profile contract through named FOI-O, archive, extraction, and
  read-only agent/MCP consumers before adding fields or mappings.

## Minimum evidence per jurisdiction

- current and historical legislation identifiers and versions;
- regulator or ombudsman guidance;
- representative request correspondence and attachments;
- decisions or case notes covering access, partial access, refusal, transfer,
  extension, fees, invalidity, information-not-held, and review where available;
- rights/licensing records and source digests;
- a terminology and process crosswalk with explicit non-equivalences.

## Acceptance criteria

- Commonwealth and NSW profiles pass schema, SHACL, rule-fixture, and
  source-provenance validation.
- NZ regression tests remain unchanged and passing.
- Cross-jurisdiction comparisons are blocked when source, temporal, sampling,
  annotation, or reliability gates are incomplete.
- Every Australian profile declares supported, unsupported, uncertain, and
  human-certified surfaces explicitly.
- Later jurisdictions reuse the profile contract without copying Commonwealth
  or NSW legal assumptions.
- A pilot go/no-go decision is recorded before implementation begins for the
  remaining jurisdictions, which proceed as separately gated tranches.
- A release-evidence bundle records tag/SHA, contract versions, capabilities,
  tests, fixtures, provenance, empirical results, exceptions, migrations, and
  limitations for downstream paper updates.

## Out of scope

- legal advice or automated certification;
- direct source capture from Alaveteli;
- replacing `edithatogo/legislation` or `fyi-archive`;
- treating `fe-reader` as a required dependency.
