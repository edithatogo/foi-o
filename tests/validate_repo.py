from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foi_o_nz.validation import validate_json_schema, validate_rdf, validate_schema_file, validate_yaml


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
    return pairs


def main() -> None:
    errors: list[str] = []
    for schema_path in sorted(Path("schemas/json").glob("*.schema.json")):
        errors.extend(validate_schema_file(schema_path).errors)
    for ttl_path in [*Path("ontology").glob("*.ttl"), *Path("vocab").glob("*.ttl"), *Path("shacl").glob("*.ttl")]:
        errors.extend(validate_rdf(ttl_path).errors)
    for yaml_path in Path("mappings").glob("*.yaml"):
        errors.extend(validate_yaml(yaml_path).errors)
    for instance, schema in _example_pairs():
        errors.extend(f"{instance}: {error}" for error in validate_json_schema(instance, schema).errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository validation ok")


if __name__ == "__main__":
    main()
