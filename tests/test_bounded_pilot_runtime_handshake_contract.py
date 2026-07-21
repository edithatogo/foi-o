from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).parents[1]
PROMPT = ROOT / "examples/v2/bounded-pilot-analyst-prompts/runtime-handshake.v0.2.txt"


def test_runtime_handshake_prompt_is_context_free_and_inert() -> None:
    text = PROMPT.read_text(encoding="utf-8")
    assert "No request context" in text
    assert "Do not read" in text
    assert "separately verified exact authorization" in text
    assert len(sha256(PROMPT.read_bytes()).hexdigest()) == 64
