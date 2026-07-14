# Australian FOI jurisdiction profiles

## Overview

Extend FOI-O from its validated NZ profile to evidence-backed Australian
profiles without weakening the jurisdiction-neutral core or treating Australian
information-access regimes as legally interchangeable.

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

## Out of scope

- legal advice or automated certification;
- direct source capture from Alaveteli;
- replacing `edithatogo/legislation` or `fyi-archive`;
- treating `fe-reader` as a required dependency.
