from __future__ import annotations

import importlib
import sys

import pytest

from foi_o_nz import encoding


def test_orjson_module_not_found_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that encoding gracefully falls back to stdlib json when orjson is missing."""
    # Hide orjson from sys.modules
    monkeypatch.setitem(sys.modules, "orjson", None)  # type: ignore[arg-type]

    # Reload the module to trigger the try/except block
    importlib.reload(encoding)

    try:
        assert encoding.orjson is None

        # Test dumps_json fallback
        data = {"b": 2, "a": 1}
        dumped = encoding.dumps_json(data, sort_keys=True)
        # Verify the fallback output format (which defaults to stdlib format, either pretty or not)
        assert dumped in {'{"a": 1, "b": 2}', '{"a":1,"b":2}'}

        dumped_pretty = encoding.dumps_json(data, pretty=True, sort_keys=True)
        assert dumped_pretty == '{\n  "a": 1,\n  "b": 2\n}'

        dumped_no_sort = encoding.dumps_json(data, sort_keys=False)
        assert dumped_no_sort in {'{"b": 2, "a": 1}', '{"b":2,"a":1}'}

        # Test loads_json fallback
        loaded = encoding.loads_json(b'{"a": 1}')
        assert loaded == {"a": 1}

    finally:
        # Restore the original state by removing the mock and reloading
        monkeypatch.undo()
        importlib.reload(encoding)


def test_dumps_json_with_orjson() -> None:
    """Test dumps_json with orjson available."""
    if encoding.orjson is None:
        pytest.skip("orjson is not installed")

    data = {"b": 2, "a": 1}

    dumped = encoding.dumps_json(data, sort_keys=True)
    assert dumped == '{"a":1,"b":2}'

    dumped_pretty = encoding.dumps_json(data, pretty=True, sort_keys=True)
    assert dumped_pretty == '{\n  "a": 1,\n  "b": 2\n}'

    dumped_no_sort = encoding.dumps_json(data, sort_keys=False)
    assert dumped_no_sort == '{"b":2,"a":1}'


def test_loads_json_with_orjson() -> None:
    """Test loads_json with orjson available."""
    if encoding.orjson is None:
        pytest.skip("orjson is not installed")

    loaded = encoding.loads_json(b'{"a": 1}')
    assert loaded == {"a": 1}


def test_loads_json_string_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loads_json fallback with string input."""
    monkeypatch.setitem(sys.modules, "orjson", None)  # type: ignore[arg-type]
    importlib.reload(encoding)
    try:
        loaded = encoding.loads_json('{"a": 1}')
        assert loaded == {"a": 1}
    finally:
        monkeypatch.undo()
        importlib.reload(encoding)
