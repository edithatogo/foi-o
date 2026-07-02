from __future__ import annotations

from pathlib import Path

from foi_o_nz.validation import (
    validate_json_schema,
    validate_rdf,
    validate_schema_file,
    validate_yaml,
)


def test_json_schemas_are_valid() -> None:
    for schema_path in Path("schemas/json").glob("*.schema.json"):
        result = validate_schema_file(schema_path)
        assert result.ok, result.errors


def test_examples_validate_against_schemas() -> None:
    pairs = [
        (
            Path("examples/core-event.extension-notified.json"),
            Path("schemas/json/core-event.schema.json"),
        ),
        (
            Path("examples/agent-action.search-plan.json"),
            Path("schemas/json/agent-action.schema.json"),
        ),
    ]
    for instance, schema in pairs:
        result = validate_json_schema(instance, schema)
        assert result.ok, result.errors


def test_rdf_files_parse() -> None:
    for ttl_path in [
        *Path("ontology").glob("*.ttl"),
        *Path("vocab").glob("*.ttl"),
        *Path("shacl").glob("*.ttl"),
    ]:
        result = validate_rdf(ttl_path)
        assert result.ok, result.errors


def test_yaml_mappings_parse() -> None:
    for yaml_path in Path("mappings").glob("*.yaml"):
        result = validate_yaml(yaml_path)
        assert result.ok, result.errors
