"""Build locked, local-only runtime-handshake evidence without enabling analysis."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
RECORDED_AT = "2026-07-19T10:00:36+10:00"
AUTHORIZATION_COMMIT = "393991ea0cfdaf9f016108bf74edae94b80f042a"
AUTHORIZATION_SHA256 = "de140e1397df2f1e20aa9ceede443d589d6bacbca9a767fecc2992644f1c056f"
HANDSHAKE_PROMPT_SHA256 = "6fb5386e21364f172289d563c17b7c93ea17b7a2eea454ff1affa8767d1bea77"
PROHIBITED = [
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "gold_promotion",
    "legal_certification",
    "paper_update",
    "human_reviewed_claims",
    "empirical_evidence_claims",
]
ROLES = {
    "orchestrator": {
        "actor_id": "agent:orchestrator-fixture-stream",
        "role": "orchestrator_non_labeling",
        "locator": "/root/fixture_stream_ready",
        "reported_runtime_family": "GPT-5 / Codex",
        "raw_reply": """1. Canonical task/session locator: `/root/fixture_stream_ready`
2. Provider family: OpenAI
3. Model/runtime family: GPT-5 / Codex
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
    },
    "analyst_a": {
        "actor_id": "agent:analyst-fixture-a",
        "role": "analyst",
        "locator": "/root/fixture_analyst_a_ready",
        "reported_runtime_family": "Codex / GPT-5",
        "raw_reply": """1. Canonical task locator: `/root/fixture_analyst_a_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex / GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
    },
    "analyst_b": {
        "actor_id": "agent:analyst-fixture-b",
        "role": "analyst",
        "locator": "/root/fixture_analyst_b_ready",
        "reported_runtime_family": "Codex, GPT-5",
        "raw_reply": """1. Canonical task/session locator: `/root/fixture_analyst_b_ready`
2. Provider family: OpenAI
3. Model/runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session/agent UUID: unavailable
""",
    },
    "reconciler": {
        "actor_id": "agent:reconciler-fixture",
        "role": "reconciler",
        "locator": "/root/fixture_reconciler_ready",
        "reported_runtime_family": "Codex, GPT-5",
        "raw_reply": """1. Canonical task or session locator: `/root/fixture_reconciler_ready`
2. Provider family: OpenAI
3. Model or runtime family: Codex, GPT-5
4. Exact model snapshot: unavailable
5. Immutable session or agent UUID: unavailable
""",
    },
}


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _pin(path: str, physical_path: Path) -> dict[str, str]:
    return {"path": path, "sha256": sha256(physical_path.read_bytes()).hexdigest()}


def main(output: Path = PACKET, *, repository_root: Path = ROOT) -> None:
    root = repository_root.resolve(strict=True)
    authorization_path = (
        root / "examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json"
    )
    if sha256(authorization_path.read_bytes()).hexdigest() != AUTHORIZATION_SHA256:
        raise ValueError("runtime-handshake authorization SHA-256 mismatch")
    prompt_path = (
        root / "examples/v2/analyst-fixture-packet/prompts/runtime-provenance-handshake.v1.txt"
    )
    if sha256(prompt_path.read_bytes()).hexdigest() != HANDSHAKE_PROMPT_SHA256:
        raise ValueError("runtime-handshake prompt SHA-256 mismatch")
    output.mkdir(parents=True, exist_ok=True)
    evidence_pins: dict[str, dict[str, str]] = {}
    for name, role in ROLES.items():
        raw_name = f"runtime-handshake-reply.{name}.txt"
        raw_path = output / raw_name
        raw_path.write_text(role["raw_reply"], encoding="utf-8")
        record_name = f"runtime-handshake-evidence.{name}.json"
        record_path = output / record_name
        _write_json(
            record_path,
            {
                "schema_version": "foi-o.fixture-runtime-handshake-evidence.v0.1.0",
                "evidence_id": f"local-fixture-runtime-handshake-{name}-2026-07-19",
                "status": "captured_runtime_handshake_only",
                "role_key": name,
                "actor_id": role["actor_id"],
                "role": role["role"],
                "canonical_session_locator": role["locator"],
                "provider_family": "OpenAI",
                "reported_runtime_family": role["reported_runtime_family"],
                "normalized_runtime_family": "Codex / GPT-5",
                "exact_model_snapshot_available": False,
                "exact_model_snapshot": None,
                "immutable_session_agent_uuid_available": False,
                "immutable_session_agent_uuid": None,
                "delivery_time_available": False,
                "delivered_at": None,
                "reply_time_available": False,
                "reply_at": None,
                "recorded_at": RECORDED_AT,
                "recording_note": "recorded_at is repository provenance and is not a delivery or reply time",
                "handshake_authorization": {
                    "path": "examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json",
                    "sha256": AUTHORIZATION_SHA256,
                    "repository_commit": AUTHORIZATION_COMMIT,
                },
                "handshake_prompt": {
                    "path": "examples/v2/analyst-fixture-packet/prompts/runtime-provenance-handshake.v1.txt",
                    "sha256": HANDSHAKE_PROMPT_SHA256,
                },
                "raw_reply": _pin(f"examples/v2/analyst-fixture-packet/{raw_name}", raw_path),
                "raw_reply_text": role["raw_reply"],
                "handshake_prompt_delivered": True,
                "fixture_context_delivered_with_handshake": False,
                "label_material_delivered_with_handshake": False,
                "peer_output_delivered_with_handshake": False,
                "context_presentation_allowed": False,
                "analysis_execution_allowed": False,
                "reconciliation_allowed": False,
                "local_only": True,
                "empirical_evidence": False,
                "human_reviewed": False,
                "gold_eligible": False,
                "release_qualifying": False,
                "publication_eligible": False,
            },
        )
        evidence_pins[name] = _pin(f"examples/v2/analyst-fixture-packet/{record_name}", record_path)
    _write_json(
        output / "runtime-handshake-readiness.locked.json",
        {
            "schema_version": "foi-o.fixture-runtime-handshake-readiness.v0.1.0",
            "status": "locked_runtime_handshake_evidence_final_execution_wrapper_pending",
            "recorded_at": RECORDED_AT,
            "handshake_authorization": {
                "path": "examples/v2/analyst-fixture-packet/runtime-handshake-authorization.approved.json",
                "sha256": AUTHORIZATION_SHA256,
                "repository_commit": AUTHORIZATION_COMMIT,
            },
            "evidence_records": evidence_pins,
            "runtime_handshakes_complete": True,
            "role_count": 4,
            "exact_model_snapshots_available": False,
            "immutable_session_agent_uuids_available": False,
            "context_presentation_allowed": False,
            "analysis_execution_allowed": False,
            "reconciliation_allowed": False,
            "final_execution_wrapper_present": False,
            "execution_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )


if __name__ == "__main__":
    main()
