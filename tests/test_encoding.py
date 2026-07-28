import importlib

from foi_o_nz import encoding


def test_orjson_module_not_found_fallback(monkeypatch):
    """Test that when orjson is not available, the module falls back gracefully."""
    # We use monkeypatch to temporarily block importing orjson
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name in {"orjson", "orjson as _orjson"}:
            raise ModuleNotFoundError("No module named 'orjson'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)

    # Reload the module to trigger the except ModuleNotFoundError block
    importlib.reload(encoding)

    try:
        assert encoding.orjson is None

        # Test fallback loads_json
        assert encoding.loads_json('{"test": 1}') == {"test": 1}
        assert encoding.loads_json(b'{"test": 1}') == {"test": 1}
        assert encoding.loads_json(bytearray(b'{"test": 1}')) == {"test": 1}

        # Test fallback dumps_json
        assert encoding.dumps_json({"test": 1}) == '{"test": 1}'
        assert encoding.dumps_json({"test": 1}, pretty=True) == '{\n  "test": 1\n}'
    finally:
        # We need to reload the module again with the original import
        # so subsequent tests won't fail
        monkeypatch.undo()
        importlib.reload(encoding)
        assert encoding.orjson is not None


def test_orjson_fast_path():
    """Test that orjson is used when available."""
    assert encoding.orjson is not None

    # Test fast loads_json
    assert encoding.loads_json('{"test": 1}') == {"test": 1}
    assert encoding.loads_json(b'{"test": 1}') == {"test": 1}
    assert encoding.loads_json(bytearray(b'{"test": 1}')) == {"test": 1}

    # Test fast dumps_json
    assert encoding.dumps_json({"test": 1}) == '{"test":1}'
    assert encoding.dumps_json({"test": 1}, pretty=True) == '{\n  "test": 1\n}'
    assert encoding.dumps_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert encoding.dumps_json({"b": 2, "a": 1}, sort_keys=False) == '{"b":2,"a":1}'
