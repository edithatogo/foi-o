import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.validation import validate_json_schema
from scripts.build_fixture_runtime_handshake_evidence import main as build_evidence

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
ROLES = ("orchestrator", "analyst_a", "analyst_b", "reconciler")
EXPECTED_RAW = {
    "orchestrator": """1. Canonical task/session locator: `/root/fixture_stream_ready`
2. Provider family: OpenAI
3. Model/runtime family: GPT-5 / Codex
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
    "analyst_a": """1. Canonical task locator: `/root/fixture_analyst_a_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex / GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
    "analyst_b": """1. Canonical task/session locator: `/root/fixture_analyst_b_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session/agent UUID: unavailable
""",
    "reconciler": """1. Canonical task or session locator: `/root/fixture_reconciler_ready`
2. Provider family: OpenAI
3. Model or runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_four_handshake_records_preserve_exact_bounded_evidence() -> None:
    locators: set[str] = set()
    evidence_hashes: set[str] = set()
    for role in ROLES:
        record_path = PACKET / f"runtime-handshake-evidence.{role}.json"
        assert not validate_json_schema(
            record_path, ROOT / "schemas/json/fixture-runtime-handshake-evidence.schema.json"
        ).errors
        record = _load(record_path)
        raw_path = ROOT / record["raw_reply"]["path"]
        assert raw_path.read_text(encoding="utf-8") == EXPECTED_RAW[role]
        assert record["raw_reply_text"] == EXPECTED_RAW[role]
        assert record["raw_reply"]["sha256"] == _digest(raw_path)
        assert record["role_key"] == role
        assert record["handshake_authorization"]["sha256"] == (
            "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f"
        )
        assert record["handshake_authorization"]["repository_commit"] == (
            "393991ea0cfdaf9f016108bf74edae94b80f042a"
        )
        assert record["handshake_prompt"]["sha256"] == (
            "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77"
        )
        assert record["reply_time_available"] is False
        assert record["reply_at"] is None
        assert record["delivery_time_available"] is False
        assert record["delivered_at"] is None
        assert record["exact_model_snapshot_available"] is False
        assert record["exact_model_snapshot"] is None
        assert record["immutable_session_agent_uuid_available"] is False
        assert record["immutable_session_agent_uuid"] is None
        assert record["fixture_context_delivered_with_handshake"] is False
        assert record["label_material_delivered_with_handshake"] is False
        assert record["peer_output_delivered_with_handshake"] is False
        assert record["context_presentation_allowed"] is False
        assert record["analysis_execution_allowed"] is False
        assert record["reconciliation_allowed"] is False
        locators.add(record["canonical_session_locator"])
        evidence_hashes.add(_digest(record_path))
    assert len(locators) == len(evidence_hashes) == 4


def test_locked_readiness_pins_exact_four_records_and_keeps_execution_disabled() -> None:
    readiness_path = PACKET / "runtime-handshake-readiness.locked.json"
    assert not validate_json_schema(
        readiness_path, ROOT / "schemas/json/fixture-runtime-handshake-readiness.schema.json"
    ).errors
    readiness = _load(readiness_path)
    assert set(readiness["evidence_records"]) == set(ROLES)
    for role, pin in readiness["evidence_records"].items():
        assert pin["path"].endswith(f"runtime-handshake-evidence.{role}.json")
        assert pin["sha256"] == _digest(ROOT / pin["path"])
    assert readiness["runtime_handshakes_complete"] is True
    assert readiness["final_execution_wrapper_present"] is False
    assert readiness["execution_allowed"] is False
    assert readiness["context_presentation_allowed"] is False
    assert readiness["analysis_execution_allowed"] is False
    assert readiness["reconciliation_allowed"] is False
    for key in (
        "empirical_evidence",
        "human_reviewed",
        "gold_eligible",
        "release_qualifying",
        "publication_eligible",
    ):
        assert readiness[key] is False


def test_handshake_evidence_builder_is_byte_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    build_evidence(output, repository_root=ROOT)
    expected_names = {
        "runtime-handshake-readiness.locked.json",
        *{f"runtime-handshake-evidence.{role}.json" for role in ROLES},
        *{f"runtime-handshake-reply.{role}.txt" for role in ROLES},
    }
    assert {path.name for path in output.iterdir()} == expected_names
    for name in expected_names:
        assert (output / name).read_bytes() == (PACKET / name).read_bytes()
