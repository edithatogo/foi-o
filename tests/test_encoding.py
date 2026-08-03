"""Contract tests for optional fast JSON encoding and its stdlib fallback."""

from __future__ import annotations

import importlib
import sys

from foi_o_nz import encoding


def test_encoding_fallback_when_orjson_is_unavailable(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "orjson", None)
    importlib.reload(encoding)

    assert encoding.orjson is None
    assert encoding.loads_json('{"a": 1}') == {"a": 1}
    assert encoding.loads_json(b'{"a": 1}') == {"a": 1}
    assert encoding.loads_json(bytearray(b'{"a": 1}')) == {"a": 1}
    assert encoding.dumps_json({"a": 1}) == '{"a": 1}'
    assert encoding.dumps_json({"a": 1}, pretty=True) == '{\n  "a": 1\n}'
    assert encoding.dumps_json({"b": 2, "a": 1}, sort_keys=True) == '{"a": 1, "b": 2}'

    monkeypatch.delitem(sys.modules, "orjson", raising=False)
    importlib.reload(encoding)


def test_encoding_fast_path_when_orjson_is_available() -> None:
    if encoding.orjson is None:
        return
    assert encoding.loads_json('{"a": 1}') == {"a": 1}
    assert encoding.dumps_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert encoding.dumps_json({"a": 1}, pretty=True) == '{\n  "a": 1\n}'
