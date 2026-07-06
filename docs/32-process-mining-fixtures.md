# Process Mining Fixtures

FOI-O NZ now includes fixture-only process-mining exports. These artefacts make
the event-log boundary explicit for tools that consume XES or OCEL-style data.
They do not introduce another jurisdiction, do not access live FYI/archive data,
and the fixture does not prove process performance.

## Artefacts

| Artefact | Role | Generation command |
| --- | --- | --- |
| `examples/process-mining-events.fixture.jsonl` | Small committed FOI-O NZ event log using core event fields. | Maintained as a fixture. |
| `examples/process-mining.fixture.xes` | XES import fixture for process-mining tools. | `uv run foi-o-nz export-process-mining --format xes --events examples/process-mining-events.fixture.jsonl --output examples/process-mining.fixture.xes` |
| `examples/process-mining.fixture.ocel.json` | OCEL-style JSON import fixture for object-centric process-mining review. | `uv run foi-o-nz export-process-mining --format ocel --events examples/process-mining-events.fixture.jsonl --output examples/process-mining.fixture.ocel.json` |
| `examples/process-mining-conformance.fixture.json` | Fixture-only conformance report for the expected release path. | `uv run foi-o-nz process-mining-conformance --events examples/process-mining-events.fixture.jsonl --output examples/process-mining-conformance.fixture.json` |
| `schemas/json/process-mining-ocel.schema.json` | Machine-readable contract for the OCEL fixture. | Validated by `uv run python scripts/validate_examples.py`. |
| `schemas/json/process-mining-conformance.schema.json` | Machine-readable contract for the fixture conformance report. | Validated by `uv run python scripts/validate_examples.py`. |

## Mapping To The Process Models

The fixture event sequence maps one request case through observation,
registration, deadline calculation, search planning, decision-pack drafting,
human certification, decision communication, release, and closure.

The mapping supports three checks:

- event-log import into process-mining tooling through XES;
- object/request-centric import through the OCEL-style JSON fixture;
- preservation of the human-certification boundary before decision
  communication and release.
- fixture-only conformance of the observed activity sequence against the
  expected release path.

The mapping is intentionally smaller than the BPMN and Petri net models in
`docs/31-process-models.md`. It exercises a normal release path, not every
branch, exception, consultation, charge, refusal, complaint, or disclosure-log
path.

## Claim Boundary

These fixtures are annotation and interoperability artefacts only. They are
not a human-reviewed gold standard, not a live corpus sample, and not evidence
of agency cycle times, compliance rates, bottlenecks, or variant frequencies.

Before making empirical process-mining claims, the project needs a documented
task set, source register entries for each sampled request, human review status,
and a conformance report that separates observed events from inferred or
candidate events.
