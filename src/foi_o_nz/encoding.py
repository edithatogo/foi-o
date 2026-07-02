"""Fast JSON encoding helpers with a strict standard-library fallback."""

from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover - depends on optional runtime wheel availability
    import orjson
except ModuleNotFoundError:  # pragma: no cover - exercised only without orjson
    orjson = None  # type: ignore[assignment]


def loads_json(data: str | bytes | bytearray) -> Any:
    """Load JSON using orjson when available, otherwise the stdlib parser."""
    if orjson is not None:
        return orjson.loads(data)
    if isinstance(data, bytes | bytearray):
        data = data.decode("utf-8")
    return json.loads(data)


def dumps_json(data: Any, *, pretty: bool = False, sort_keys: bool = True) -> str:
    """Dump JSON as UTF-8 text with deterministic defaults."""
    if orjson is not None:
        option = 0
        if sort_keys:
            option |= orjson.OPT_SORT_KEYS
        if pretty:
            option |= orjson.OPT_INDENT_2
        option |= orjson.OPT_NAIVE_UTC
        return orjson.dumps(data, option=option, default=str).decode("utf-8")
    return json.dumps(
        data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=sort_keys, default=str
    )
