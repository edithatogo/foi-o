# Specification: Event extraction timeline and provenance

## Objective

Harden observed correspondence event extraction, timeline reconstruction, event confidence/provenance, and evaluation fixtures.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/13
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Extract observed correspondence events from public manifest/message fields without certifying legal outcomes.
- Reconstruct request timelines with deterministic ordering and explicit source/evidence references.
- Distinguish observed, inferred, asserted, certified, and unknown status in examples and evaluation fixtures.
- Add evaluation data for event precision/recall style checks using safe committed fixtures.
- Preserve the human certification boundary for decision, release, refusal, redaction, charge, extension, transfer, and complaint outcomes.

## Acceptance Criteria

- Event extraction tests cover message observation, candidate event detection, timeline ordering, confidence, and provenance.
- Evaluation commands run on committed fixtures and produce deterministic output.
- Quality gates flag uncertified dispositive outcomes.
- Documentation clearly separates extraction candidates from certified facts.
