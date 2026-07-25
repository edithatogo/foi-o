# jurisdiction onboarding and capability maturity

This track implements the live FOI-O global programme slice for **FOIO-REQ-JUR-001**. It preserves existing NZ evidence, uses immutable cross-repository references, and fails closed at human gates.

## Incremental completion contract

Every jurisdiction or deployment in `profiles/roadmap.yaml` must eventually complete all six phases recorded in `conductor/jurisdiction-completion-map.yaml`: official legislation access; Gazette or equivalent evidence; bounded `fyi-cli` capture; immutable `fyi-archive` preservation; governed `nlp-policy-nz` extraction; and provenance-bearing FOI case/process modelling in `foi-process` and FOI-O.

Delivery remains incremental. A tranche or jurisdiction may advance only on its own evidence, and completion in one repository does not imply another phase is complete. The programme must not infer legal outcomes from platform state, import rules across profiles without a crosswalk, or promote a profile automatically.

## Acceptance

- The coverage map contains every target in the roadmap exactly once and every required phase has a named owner repository.
- Each owner repository has a cross-referenced GitHub issue and Conductor track.
- Per-jurisdiction work records source identity, temporal scope, acquisition method, rights, hashes, extractor/ontology versions, positive and negative examples, and independent review boundaries.
- Live capture, rights decisions, legal/profile promotion, and publication remain explicit human gates.
