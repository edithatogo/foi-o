🧪 Add tests for encoding.py ModuleNotFoundError fallback

🎯 **What:** Tested the `ModuleNotFoundError` fallback when importing `orjson` in `src/foi_o_nz/encoding.py` falls back to the standard library `json` parsing.

📊 **Coverage:** Covered both `dumps_json` and `loads_json` functions when `orjson` is not installed as well as functional coverage when it is installed. Reached 100% coverage on `encoding.py`.

✨ **Result:** Improved test coverage and ensured reliability when the optional `orjson` dependency is missing from the environment.
