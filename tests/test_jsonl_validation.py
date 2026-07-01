from __future__ import annotations

import json
from pathlib import Path

from foi_o_nz.validation import validate_jsonl_schema


def test_validate_jsonl_schema(tmp_path: Path) -> None:
    schema = tmp_path / "schema.json"
    schema.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
                "additionalProperties": False,
            }
        ),
        encoding="utf-8",
    )
    data = tmp_path / "data.jsonl"
    data.write_text('{"id": 1}\n', encoding="utf-8")

    result = validate_jsonl_schema(data, schema)

    assert result.ok
