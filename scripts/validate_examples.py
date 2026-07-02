"""Validate repository examples from the command line."""

from __future__ import annotations

from pathlib import Path

from foi_o_nz.validation import validate_json_schema

PAIR_GLOBS = [
    ("core-event*.json", "core-event.schema.json"),
    ("agent-action*.json", "agent-action.schema.json"),
    ("request*.jsonld", "request-profile.schema.json"),
    ("run-manifest*.json", "run-manifest.schema.json"),
    ("embedding-record*.json", "embedding-record.schema.json"),
    ("event-evaluation*.json", "event-evaluation.schema.json"),
    ("transition-audit*.json", "transition-audit.schema.json"),
    ("chunk-record*.json", "chunk-record.schema.json"),
    ("ledger-entry*.json", "ledger-entry.schema.json"),
    ("quality-report*.json", "quality-report.schema.json"),
    ("risk-assessment*.json", "risk-assessment.schema.json"),
    ("dataset-metadata*.json", "dataset-metadata.schema.json"),
    ("retrieval-result*.json", "retrieval-result.schema.json"),
    ("redaction-candidate*.json", "redaction-candidate.schema.json"),
    ("diff-report*.json", "diff-report.schema.json"),
    ("agent-pack*.json", "agent-pack.schema.json"),
    ("reproducibility-manifest*.json", "reproducibility-manifest.schema.json"),
    ("cas-manifest*.json", "cas-manifest.schema.json"),
    ("lineage-graph*.json", "lineage-graph.schema.json"),
    ("trace-span*.json", "trace-span.schema.json"),
    ("goldset-task*.json", "goldset-task.schema.json"),
    ("guardrail-replay*.json", "guardrail-replay.schema.json"),
    ("nz-public-holidays*.json", "holiday-calendar.schema.json"),
    ("mojo-audit*.json", "mojo-audit.schema.json"),
    ("kernel-manifest*.json", "kernel-manifest.schema.json"),
    ("kernel-readiness*.json", "kernel-readiness.schema.json"),
]


def _pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for glob, schema_name in PAIR_GLOBS:
        pairs.extend(
            (path, Path("schemas/json") / schema_name)
            for path in sorted(Path("examples").glob(glob))
        )
    return pairs


def main() -> None:
    """Run example validation."""
    errors: list[str] = []
    for instance, schema in _pairs():
        result = validate_json_schema(instance, schema)
        errors.extend(f"{instance}: {error}" for error in result.errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("examples ok")


if __name__ == "__main__":
    main()
