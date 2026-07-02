from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foi_o_nz.validation import (
    validate_json_schema,
    validate_rdf,
    validate_schema_file,
    validate_yaml,
)


def _example_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    pairs.extend(
        (path, Path("schemas/json/core-event.schema.json"))
        for path in sorted(Path("examples").glob("core-event*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/agent-action.schema.json"))
        for path in sorted(Path("examples").glob("agent-action*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/request-profile.schema.json"))
        for path in sorted(Path("examples").glob("request*.jsonld"))
    )
    pairs.extend(
        (path, Path("schemas/json/run-manifest.schema.json"))
        for path in sorted(Path("examples").glob("run-manifest*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/cas-manifest.schema.json"))
        for path in sorted(Path("examples").glob("cas-manifest*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/release-checklist.schema.json"))
        for path in sorted(Path("examples").glob("release-checklist*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/repository-release-metadata.schema.json"))
        for path in sorted(Path("examples").glob("repository-release-metadata*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/lineage-graph.schema.json"))
        for path in sorted(Path("examples").glob("lineage-graph*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/trace-span.schema.json"))
        for path in sorted(Path("examples").glob("trace-span*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/goldset-task.schema.json"))
        for path in sorted(Path("examples").glob("goldset-task*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/guardrail-replay.schema.json"))
        for path in sorted(Path("examples").glob("guardrail-replay*.json"))
    )

    pairs.extend(
        (path, Path("schemas/json/mojo-audit.schema.json"))
        for path in sorted(Path("examples").glob("mojo-audit*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/kernel-manifest.schema.json"))
        for path in sorted(Path("examples").glob("kernel-manifest*.json"))
    )
    pairs.extend(
        (path, Path("schemas/json/kernel-readiness.schema.json"))
        for path in sorted(Path("examples").glob("kernel-readiness*.json"))
    )
    return pairs


def main() -> None:
    errors: list[str] = []
    for schema_path in sorted(Path("schemas/json").glob("*.schema.json")):
        errors.extend(validate_schema_file(schema_path).errors)
    for ttl_path in [
        *Path("ontology").glob("*.ttl"),
        *Path("vocab").glob("*.ttl"),
        *Path("shacl").glob("*.ttl"),
    ]:
        errors.extend(validate_rdf(ttl_path).errors)
    for yaml_path in Path("mappings").glob("*.yaml"):
        errors.extend(validate_yaml(yaml_path).errors)
    for instance, schema in _example_pairs():
        errors.extend(
            f"{instance}: {error}" for error in validate_json_schema(instance, schema).errors
        )
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository validation ok")


if __name__ == "__main__":
    main()
