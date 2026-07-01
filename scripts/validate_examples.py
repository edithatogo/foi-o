"""Validate repository examples from the command line."""

from __future__ import annotations

from pathlib import Path

from foi_o_nz.validation import validate_json_schema

PAIRS = [
    (Path("examples/core-event.extension-notified.json"), Path("schemas/json/core-event.schema.json")),
    (Path("examples/agent-action.search-plan.json"), Path("schemas/json/agent-action.schema.json")),
]


def main() -> None:
    """Run example validation."""
    errors: list[str] = []
    for instance, schema in PAIRS:
        result = validate_json_schema(instance, schema)
        errors.extend(f"{instance}: {error}" for error in result.errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("examples ok")


if __name__ == "__main__":
    main()
