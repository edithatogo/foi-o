from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

REQUEST = Path("examples/v2/australian-nsw-rtk-all-captures-request-2026-07-24.pending.json")
SCHEMA = Path("schemas/json/australian-internet-archive-all-captures-request.schema.json")


def test_pending_all_captures_request_is_exact_and_non_executing() -> None:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    jsonschema.validate(request, schema)
    assert request["query"]["capture_mode"] == "all_captures"
    assert request["query"]["url_collapse"] is False
    assert request["authorization"]["dispatch_authorized"] is False
    assert request["retention"]["replay_authorized"] is False
    assert request["retention"]["manifest_authorized"] is False
    assert hashlib.sha256(REQUEST.read_bytes()).hexdigest()
