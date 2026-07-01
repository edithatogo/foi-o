from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from foi_o_nz.validation import validate_json_schema, validate_rdf, validate_schema_file, validate_yaml


def main() -> None:
    errors: list[str] = []
    for schema_path in sorted(Path("schemas/json").glob("*.schema.json")):
        errors.extend(validate_schema_file(schema_path).errors)
    for ttl_path in [*Path("ontology").glob("*.ttl"), *Path("vocab").glob("*.ttl"), *Path("shacl").glob("*.ttl")]:
        errors.extend(validate_rdf(ttl_path).errors)
    for yaml_path in Path("mappings").glob("*.yaml"):
        errors.extend(validate_yaml(yaml_path).errors)
    pairs = [
        (Path("examples/core-event.extension-notified.json"), Path("schemas/json/core-event.schema.json")),
        (Path("examples/agent-action.search-plan.json"), Path("schemas/json/agent-action.schema.json")),
    ]
    for instance, schema in pairs:
        errors.extend(f"{instance}: {error}" for error in validate_json_schema(instance, schema).errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("repository validation ok")


if __name__ == "__main__":
    main()
