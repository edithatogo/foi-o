# Event extraction timeline validation

Date: 2026-07-02

Scope: Track closeout validation for event extraction, timeline reconstruction,
event-evaluation fixtures, schema/example contracts, and local quality gates.

## Commands

| Command | Result |
|---|---|
| `uv run pytest -q tests/test_event_extraction_timeline.py tests/test_evaluation.py tests/test_quality.py tests/test_transitions.py tests/test_validation.py tests/test_jsonl_validation.py` | Passed, 18 tests. |
| `uv run python scripts/validate_examples.py` | Passed, `examples ok`. |
| `uv run foi-o-nz validate-repo` | Passed, `repository validation ok`. |
| `uv run ruff check src tests scripts` | Passed. |
| `uv run ruff format --check src tests scripts` | Passed, 89 files already formatted. |

## Boundary Notes

- Event extraction and timeline reconstruction are deterministic process-model
  aids, not legal determinations.
- Event evaluation compares extractor keys against fixture gold records for
  quality measurement only.
- Candidate decision, release, refusal, charge, extension, transfer, complaint,
  and redaction-like outcomes remain subject to human certification and review
  gates.
