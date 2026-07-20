import json
from hashlib import sha256
from pathlib import Path

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
EVIDENCE_SCHEMA = ROOT / "schemas/json/bounded-pilot-runtime-handshake-evidence-v0.2.schema.json"
READINESS = ROOT / "examples/v2/bounded-pilot-runtime-handshake-readiness.locked.json"
READINESS_SCHEMA = ROOT / "schemas/json/bounded-pilot-runtime-handshake-readiness-v0.2.schema.json"
REPLY_KEYS = ("actor_id", "actor_class", "role", "provider", "model", "session_id", "role_prompt_sha256", "handshake_prompt_sha256", "context_received", "candidate_labels_received", "peer_outputs_received", "ready_for_future_exact_authorization")


def test_three_runtime_handshakes_are_exact_context_free_and_distinct() -> None:
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    assert not validate_json_schema(READINESS, READINESS_SCHEMA).errors
    actors: list[str] = []
    sessions: list[str] = []
    for pin in readiness["evidence"]:
        path = ROOT / pin["path"]
        assert sha256(path.read_bytes()).hexdigest() == pin["sha256"]
        assert not validate_json_schema(path, EVIDENCE_SCHEMA).errors
        evidence = json.loads(path.read_text(encoding="utf-8"))
        reply = {key: evidence["handshake_prompt"]["sha256"] if key == "handshake_prompt_sha256" else evidence[key] for key in REPLY_KEYS}
        encoded = json.dumps(reply, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        assert sha256(encoded).hexdigest() == evidence["reply_sha256"]
        assert not evidence["context_received"]
        assert not evidence["candidate_labels_received"]
        assert not evidence["peer_outputs_received"]
        actors.append(evidence["actor_id"])
        sessions.append(evidence["session_id"])
    assert len(set(actors)) == len(set(sessions)) == 3
