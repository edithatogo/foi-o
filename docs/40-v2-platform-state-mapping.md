# V2 empirical platform-state mapping

FYI and Right to Know expose source-platform states. These states are retained
exactly as observed and are not legal outcomes. A state may provide useful
routing or sampling information, but its relationship to correspondence,
attachments, process events, and legal concepts must be measured.

## Mapping unit and versioning

Mappings are platform- and time-specific. Each record identifies the raw state,
latest state where distinct, platform vocabulary observation date, mapping
version, candidate FOI-O event(s), confidence or deterministic basis, evidence
needed for upgrade, conflicts, and review status. Unknown/new states fail open to
`unknown` rather than inheriting a nearest label.

## Empirical audit

Stratify samples by raw state, including rare administrative states and state
transitions. Review correspondence and attachments where available, preserve
conflicts, and sample across years to detect changes in platform vocabulary or
user/administrator practice.

Report raw-state coverage, candidate-event precision/recall on adjudicated
constructs, unknown/abstention, conflict with visible correspondence or
attachments, temporal drift, and unsafe legal-outcome inference. A mapping may
be one-to-many; one-to-one equivalence is never assumed.

## Change control

Mapping changes are versioned and do not overwrite earlier interpretations.
Semantic changes require a change request and regression of affected gold and
negative-control cases. First/last observed dates are recorded.

## Certification boundary

A state such as `successful`, `rejected`, or `partially_successful` remains a
platform state. It cannot by itself certify full release, refusal, a statutory
ground, timeliness, or legal compliance.
