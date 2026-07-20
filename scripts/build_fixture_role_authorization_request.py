"""Build deterministic, fail-closed fixture role-authorization preparation evidence."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from foi_o_nz.analyst_packet_verification import canonical_redacted_context, derive_fixture_units

ROOT = Path(__file__).parents[1]
PACKET = ROOT / "examples/v2/analyst-fixture-packet"
PROMOTION_COMMIT = "fe875ab254ff914b18143cfe08fee202b8b532b1"
APPROVED_INPUT_READINESS_SHA256 = "814409acac7401118428bcad2d73df1b1eb8b1bf79c2fa8ce3ea0bdb560b8b6e"

ROLES = {
    "orchestrator": {
        "actor_id": "agent:orchestrator-fixture-stream",
        "role": "orchestrator_non_labeling",
        "canonical_session_locator": "/root/fixture_stream_ready",
        "may_label": False,
    },
    "analyst_a": {
        "actor_id": "agent:analyst-fixture-a",
        "role": "analyst",
        "canonical_session_locator": "/root/fixture_analyst_a_ready",
        "may_label": True,
    },
    "analyst_b": {
        "actor_id": "agent:analyst-fixture-b",
        "role": "analyst",
        "canonical_session_locator": "/root/fixture_analyst_b_ready",
        "may_label": True,
    },
    "reconciler": {
        "actor_id": "agent:reconciler-fixture",
        "role": "reconciler",
        "canonical_session_locator": "/root/fixture_reconciler_ready",
        "may_label": False,
    },
}

HANDSHAKE_PROMPT = """FOI-O fixture runtime provenance handshake v1

Report only values directly visible in your current task runtime:
1. canonical task or session locator;
2. provider family;
3. model or runtime family;
4. exact model snapshot, or unavailable;
5. immutable session or agent UUID, or unavailable.

Do not infer, guess, label fixture units, inspect another analyst output, or execute the fixture protocol.
"""

EXECUTION_PROMPTS = {
    "orchestrator": """FOI-O fixture stream orchestrator prompt v1

After an exact human-approved, committed v0.2 execution authorization passes verification, coordinate only the staged delivery and locking mechanics. Do not label units, reconcile outcomes, expose either analyst output before both complete sets are locked, or claim human review, empirical evidence, gold status, release eligibility, or publication eligibility.
""",
    "analyst_a": """FOI-O fixture analyst A prompt v1

Run only after the exact committed v0.2 execution authorization passes verification. Independently classify every authorized redacted fixture context using the pinned approved codebook. Do not inspect analyst B output, extractor candidate labels, extractor confidence, or reconciliation material. Record controlled abstention when evidence is insufficient. Keep all promotion gates disabled.
""",
    "analyst_b": """FOI-O fixture analyst B prompt v1

Run only after the exact committed v0.2 execution authorization passes verification. Independently classify every authorized redacted fixture context using the pinned approved codebook. Do not inspect analyst A output, extractor candidate labels, extractor confidence, or reconciliation material. Record controlled abstention when evidence is insufficient. Keep all promotion gates disabled.
""",
    "reconciler": """FOI-O fixture reconciler prompt v1

Run only after both authorized analyst result sets are complete and content-hash locked. Inspect only the authorized source context and those two locked sets. Reconcile every label, span, or abstention disagreement with a reasoned candidate outcome or unresolved status. Never overwrite first-pass records or claim human adjudication, empirical ground truth, gold status, release eligibility, or publication eligibility.
""",
}


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _write_json(path: Path, value: object) -> None:
    _write_bytes(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _pin(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }


def _source_value(root: Path, source_path: str, start: int, end: int) -> dict[str, Any]:
    text = (root / source_path).read_text(encoding="utf-8")
    value = json.loads(text[start:end])
    if not isinstance(value, dict):
        raise ValueError("fixture source span is not an object")
    return value


def main(output: Path = PACKET, *, repository_root: Path = ROOT) -> None:
    """Write preparation evidence without creating or approving execution authorization."""
    root = repository_root.resolve(strict=True)
    output.mkdir(parents=True, exist_ok=True)
    prompts = output / "prompts"
    handshake_path = prompts / "runtime-provenance-handshake.v1.txt"
    _write_bytes(handshake_path, HANDSHAKE_PROMPT.encode("utf-8"))

    execution_prompt_paths: dict[str, Path] = {}
    provenance_paths: dict[str, Path] = {}
    for name, role in ROLES.items():
        prompt_path = prompts / f"{name}.future-execution.v1.txt"
        _write_bytes(prompt_path, EXECUTION_PROMPTS[name].encode("utf-8"))
        execution_prompt_paths[name] = prompt_path
        record_path = output / f"role-provenance.{name}.pending.json"
        _write_json(
            record_path,
            {
                "schema_version": "foi-o.fixture-role-provenance.v0.1.0",
                "status": "pending_runtime_handshake_and_human_authorization",
                "actor_id": role["actor_id"],
                "actor_class": "automated_agent",
                "role": role["role"],
                "canonical_session_locator": role["canonical_session_locator"],
                "immutable_session_uuid_available": False,
                "immutable_session_uuid": None,
                "runtime": {
                    "provider_family": None,
                    "model_runtime_family": None,
                    "exact_snapshot_available": False,
                    "exact_snapshot": None,
                },
                "may_label": role["may_label"],
                "handshake_prompt": _pin(handshake_path, root),
                "future_execution_prompt": _pin(prompt_path, root),
                "handshake_completed": False,
                "execution_allowed": False,
            },
        )
        provenance_paths[name] = record_path

    contexts = []
    for unit in derive_fixture_units(root):
        value = _source_value(root, unit.source_path, *unit.source_span)
        encoded, removed = canonical_redacted_context(value)
        if sha256(encoded).hexdigest() != unit.context_sha256:
            raise ValueError(f"{unit.unit_id}: redacted context digest mismatch")
        contexts.append(
            {
                "unit_id": unit.unit_id,
                "unit_sha256": unit.unit_sha256,
                "context_sha256": unit.context_sha256,
                "source_path": unit.source_path,
                "source_span": {"start": unit.source_span[0], "end": unit.source_span[1]},
                "removed_keys": list(removed),
                "presented_context": json.loads(encoded),
            }
        )
    context_path = output / "context-presentation.pending.json"
    _write_json(
        context_path,
        {
            "schema_version": "foi-o.fixture-context-presentation.v0.1.0",
            "status": "prepared_not_presented",
            "canonicalization": "utf8_json_sort_keys_compact_remove_assertion_status_confidence_v1",
            "unit_count": 11,
            "contexts": contexts,
            "execution_allowed": False,
        },
    )

    isolation_path = output / "role-isolation-plan.pending.json"
    _write_json(
        isolation_path,
        {
            "schema_version": "foi-o.fixture-role-isolation-plan.v0.1.0",
            "status": "pending_execution_authorization",
            "analysts_have_distinct_locators": True,
            "analysts_receive_only_context_manifest_and_approved_codebook": True,
            "cross_analyst_output_hidden_until_both_sets_locked": True,
            "extractor_candidate_label_hidden": True,
            "extractor_confidence_hidden": True,
            "reconciler_receives_outputs_only_after_both_sets_locked": True,
            "orchestrator_may_label": False,
            "execution_allowed": False,
        },
    )

    request_path = output / "role-authorization-request.pending.json"
    _write_json(
        request_path,
        {
            "schema_version": "foi-o.fixture-role-authorization-request.v0.1.0",
            "status": "pending_exact_human_execution_authorization",
            "promotion_commit": PROMOTION_COMMIT,
            "approved_input_readiness": {
                "path": "examples/v2/analyst-fixture-packet/input-readiness.approved.json",
                "sha256": APPROVED_INPUT_READINESS_SHA256,
            },
            "handshake_prompt": _pin(handshake_path, root),
            "future_execution_prompts": {
                name: _pin(path, root) for name, path in execution_prompt_paths.items()
            },
            "role_provenance": {name: _pin(path, root) for name, path in provenance_paths.items()},
            "context_presentation": _pin(context_path, root),
            "isolation_plan": _pin(isolation_path, root),
            "human_approval_present": False,
            "approved_by": None,
            "approved_at": None,
            "execution_authorization_present": False,
            "execution_allowed": False,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": [
                "execution",
                "redistribution",
                "publication",
                "training",
                "fine_tuning",
                "release",
                "dataset_publication",
                "gold_promotion",
                "legal_certification",
                "paper_update",
            ],
        },
    )


if __name__ == "__main__":
    main()
