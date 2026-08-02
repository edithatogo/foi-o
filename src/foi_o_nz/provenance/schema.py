"""JSON Schema validation for provenance records."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "json"
_SCHEMA_FILES = (
    "transformation-contract.schema.json",
    "authorization-record.schema.json",
    "validation-attestation.schema.json",
    "provenance-envelope.schema.json",
)


@lru_cache(maxsize=1)
def _schemas() -> dict[str, dict[str, Any]]:
    return {
        name: json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8")) for name in _SCHEMA_FILES
    }


@lru_cache(maxsize=1)
def _registry() -> Registry:
    return Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in _schemas().values()]
    )


def schema_errors(instance: Any, schema_name: str) -> list[str]:
    """Return deterministic structural and format-validation errors."""
    validator = Draft202012Validator(
        _schemas()[schema_name],
        registry=_registry(),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    rendered: list[str] = []
    for error in errors:
        path = "/".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"{path}: {error.message}")
    return rendered
