"""Validation helpers for schemas, examples, RDF, and mappings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from rdflib import Graph


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Simple validation result."""

    ok: bool
    errors: tuple[str, ...] = ()

    def raise_for_errors(self) -> None:
        """Raise ValueError if validation failed."""
        if not self.ok:
            raise ValueError("\n".join(self.errors))


def load_json(path: Path) -> Any:
    """Load JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json_schema(instance_path: Path, schema_path: Path) -> ValidationResult:
    """Validate a JSON instance against a Draft 2020-12 schema."""
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = tuple(
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            validator.iter_errors(instance), key=lambda err: list(err.absolute_path)
        )
    )
    return ValidationResult(ok=not errors, errors=errors)


def validate_jsonl_schema(instance_path: Path, schema_path: Path) -> ValidationResult:
    """Validate every object in a JSONL file against a Draft 2020-12 schema."""
    from foi_o_nz.io import iter_jsonl

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for line_no, instance in enumerate(iter_jsonl(instance_path), start=1):
        for error in sorted(
            validator.iter_errors(instance), key=lambda err: list(err.absolute_path)
        ):
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            errors.append(f"line {line_no} {path}: {error.message}")
    return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_schema_file(schema_path: Path) -> ValidationResult:
    """Validate a JSON Schema document itself."""
    try:
        Draft202012Validator.check_schema(load_json(schema_path))
    except Exception as exc:  # noqa: BLE001 - return a uniform validation result
        return ValidationResult(ok=False, errors=(f"{schema_path}: {exc}",))
    return ValidationResult(ok=True)


def validate_rdf(path: Path, *, fmt: str = "turtle") -> ValidationResult:
    """Parse an RDF file."""
    graph = Graph()
    try:
        graph.parse(path, format=fmt)
    except Exception as exc:  # noqa: BLE001 - RDF parsers raise several exception types
        return ValidationResult(ok=False, errors=(f"{path}: {exc}",))
    return ValidationResult(ok=True)


def validate_yaml(path: Path) -> ValidationResult:
    """Parse a YAML file."""
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - YAML parser raises several exception types
        return ValidationResult(ok=False, errors=(f"{path}: {exc}",))
    return ValidationResult(ok=True)
