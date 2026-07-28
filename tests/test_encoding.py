import importlib
import sys

from foi_o_nz import encoding


def test_encoding_without_orjson(monkeypatch):
    """Test the fallback to the standard library json module when orjson is not available."""
    # Hide orjson to trigger ModuleNotFoundError during import
    monkeypatch.setitem(sys.modules, "orjson", None)

    # Reload the module to trigger the try-except block at the module level
    importlib.reload(encoding)

    # Ensure orjson fallback is active
    assert encoding.orjson is None

    # Test loads_json fallback
    assert encoding.loads_json('{"a": 1}') == {"a": 1}
    assert encoding.loads_json(b'{"a": 1}') == {"a": 1}
    assert encoding.loads_json(bytearray(b'{"a": 1}')) == {"a": 1}

    # Test dumps_json fallback
    # When pretty=False, it produces a compact format without spaces, typical for default json.dumps fallback or matching standard behaviour.
    assert encoding.dumps_json({"a": 1}) == '{"a": 1}'
    assert encoding.dumps_json({"a": 1}, pretty=True) == '{\n  "a": 1\n}'
    assert encoding.dumps_json({"b": 2, "a": 1}, sort_keys=True) == '{"a": 1, "b": 2}'

    # Reload again to restore the original state for other tests
    monkeypatch.undo()
    importlib.reload(encoding)
