# Ontology and jurisdiction profile versioning

## Decision

FOI-O is a versioned ontology family. It does not use long-lived Git branches
as jurisdiction boundaries.

| Artifact | Identifier example | Versioned independently | Purpose |
|---|---|---:|---|
| Core ontology | `foi-o` | Yes | Jurisdiction-neutral concepts, evidence, provenance, process primitives, and governance axes. |
| Country profile | `foi-o-nz`, `foi-o-au` | Yes | Country-wide vocabulary, legal system, shared processes, calendars, and compatibility rules. |
| Subdivision profile | `foi-o-au-nsw` | Yes | State or territory legislation, pathways, clocks, review bodies, mappings, and fixtures. |

Identifiers use lowercase BCP 47-like segments backed by ISO jurisdiction
codes. Machine-readable jurisdiction values use ISO 3166 identifiers such as
`NZ`, `AU`, and `AU-NSW`.

## Compatibility rules

1. Every release manifest identifies exactly one core ontology version.
2. Every jurisdiction profile declares its own version and a semantic-version
   range of compatible core releases.
3. A subdivision profile declares its parent country profile and compatible
   parent-version range.
4. Profiles may extend core concepts but cannot silently redefine a core term.
   A non-equivalent legal concept receives a jurisdiction-qualified identifier.
5. A release is invalid when two selected profiles claim the same identifier
   with incompatible definitions.
6. Migrations are explicit for breaking core or profile changes. Unknown major
   versions are rejected rather than guessed.
7. Legal effective time and observation time are independent of ontology
   release time. All three are recorded.

## Release and Git policy

- Use short-lived feature branches and normal pull requests for implementation.
- Publish immutable manifests and artifacts for the core and each profile.
- Tag aggregate releases when useful, but do not force every profile to advance
  when an unrelated jurisdiction changes.
- Maintain a compatibility matrix and machine-readable migration catalogue.
- Retain deprecated identifiers with replacement metadata for at least one
  supported major release.

## Current package boundary

The existing `foi-o-nz` Python distribution remains the NZ implementation while
the neutral core/profile contracts mature. The manifest does not claim that
code has already been physically split into multiple packages. A future package
split requires its own migration and backwards-compatibility gate.

## Human gates

Automated agents may draft manifests, mappings, migrations, and candidate
fixtures. Human reviewers approve stable ontology terms, legal equivalence,
gold fixtures, and jurisdiction-profile maturity.
