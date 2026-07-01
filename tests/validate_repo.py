from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import rdflib
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate_json_schemas() -> None:
    schema_paths = sorted((ROOT / "schemas/json").glob("*.schema.json"))
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)


def validate_examples() -> None:
    pairs = [
        ("schemas/json/request-profile.schema.json", "examples/request-record.jsonld"),
        ("schemas/json/core-event.schema.json", "examples/core-event.extension-notified.json"),
        ("schemas/json/agent-action.schema.json", "examples/agent-action.search-plan.json"),
    ]
    for schema_path, example_path in pairs:
        schema = load_json(schema_path)
        example = load_json(example_path)
        jsonschema.validate(example, schema)


def validate_yaml() -> None:
    for path in sorted((ROOT / "mappings").glob("*.yaml")):
        yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_rdf() -> None:
    for folder in ["ontology", "vocab", "shacl"]:
        for path in sorted((ROOT / folder).glob("*.ttl")):
            graph = rdflib.Graph()
            graph.parse(path, format="turtle")


def main() -> None:
    validate_json_schemas()
    validate_examples()
    validate_yaml()
    validate_rdf()
    print("FOI-O NZ validation passed")


if __name__ == "__main__":
    main()
