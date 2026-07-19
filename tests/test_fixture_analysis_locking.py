import json
import shutil
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.analyst_packet_verification import verify_locked_fixture_analysis
from foi_o_nz.validation import validate_json_schema
from scripts.build_locked_fixture_analysis_sets import ROLE, build

ROOT = Path(__file__).parents[1]


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    packet = root / "examples/v2/analyst-fixture-packet"
    packet.mkdir(parents=True)
    (root / "schemas/json").mkdir(parents=True)
    for name in (
        "context-presentation.pending.json",
        "codebook.approved.json",
        "execution-authorization.v0.2.pending-verification.json",
    ):
        shutil.copy(ROOT / "examples/v2/analyst-fixture-packet" / name, packet / name)
    for name in (
        "analyst-fixture-analysis-set.schema.json",
        "analyst-fixture-analysis-lock.schema.json",
    ):
        shutil.copy(ROOT / "schemas/json" / name, root / "schemas/json" / name)
    return root


def _responses(root: Path, key: str) -> list[dict[str, object]]:
    packet = root / "examples/v2/analyst-fixture-packet"
    contexts = json.loads((packet / "context-presentation.pending.json").read_text())["contexts"]
    revision = json.loads((packet / "codebook.approved.json").read_text())["revision"]
    actor, prompt, session = ROLE[key]
    return [
        {
            "unit_id": item["unit_id"],
            "schema_version": "foi-o.locked-analyst-record.v0.1.0",
            "record_id": (
                f"analyst-a:{item['unit_id']}" if key == "a" else f"analyst-b-{item['unit_id']}"
            ),
            "status": "locked_agent_analysis",
            "analyst": {
                "actor_id": actor,
                "actor_class": "automated_agent",
                "role": "analyst",
                "runtime": {
                    "provider": "OpenAI",
                    "model": "Codex / GPT-5; exact snapshot unavailable",
                    "prompt_sha256": prompt,
                    "session_id": session,
                },
            },
            "unit_sha256": item["unit_sha256"],
            "codebook_revision": revision,
            "label": "observed",
            "span": None,
            "uncertainty": 0.1,
            "abstention": False,
            "abstention_reason": None,
            "notes": "Synthetic fixture classification.",
            "independence": {
                "blinded_to_peer_outputs": True,
                "blinded_to_candidate": True,
                "context_sha256": item["context_sha256"],
            },
            "created_at": "2026-07-19T03:19:01Z",
            "locked_at": "2026-07-19T03:19:01Z",
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
        }
        for item in contexts
    ]


def test_builder_is_deterministic_and_hash_locks_every_record(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    raw_paths = []
    for key in ("a", "b"):
        path = root / f"raw-{key}.json"
        path.write_text(json.dumps(_responses(root, key)))
        raw_paths.append(path)
    output = root / "examples/v2/analyst-fixture-packet/results"
    build(
        repository_root=root,
        analyst_a_path=raw_paths[0],
        analyst_b_path=raw_paths[1],
        output=output,
    )
    first = {path.name: path.read_bytes() for path in output.iterdir()}
    build(
        repository_root=root,
        analyst_a_path=raw_paths[0],
        analyst_b_path=raw_paths[1],
        output=output,
    )
    assert first == {path.name: path.read_bytes() for path in output.iterdir()}
    schema = ROOT / "schemas/json/analyst-fixture-analysis-set.schema.json"
    for key in ("a", "b"):
        path = output / f"analysis-set.analyst-{key}.locked.json"
        assert not validate_json_schema(path, schema).errors
        value = json.loads(path.read_text())
        for entry in value["entries"]:
            canonical = json.dumps(
                entry["record"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
            assert entry["record_sha256"] == sha256(canonical).hexdigest()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "reordered",
        "wrong_context",
        "wrong_role",
        "wrong_label",
        "wrong_record_id",
        "empty_span",
    ],
)
def test_builder_rejects_non_governed_responses(tmp_path: Path, mutation: str) -> None:
    root = _sandbox(tmp_path)
    a, b = _responses(root, "a"), _responses(root, "b")
    if mutation == "missing":
        a.pop()
    elif mutation == "reordered":
        a[0], a[1] = a[1], a[0]
    elif mutation == "wrong_context":
        a[0]["independence"]["context_sha256"] = "0" * 64  # type: ignore[index]
    elif mutation == "wrong_role":
        a[0]["analyst"]["actor_id"] = "agent:analyst-fixture-b"  # type: ignore[index]
    elif mutation == "wrong_label":
        a[0]["label"] = "not-in-codebook"
    elif mutation == "wrong_record_id":
        a[0]["record_id"] = "analysis:other:a"
    else:
        a[0]["span"] = {"start": 2, "end": 2, "coordinate_system": "utf8_character_half_open"}
    pa, pb = root / "a.json", root / "b.json"
    pa.write_text(json.dumps(a))
    pb.write_text(json.dumps(b))
    with pytest.raises(ValueError, match=r"responses|digest|identity|label|record ID|span"):
        build(repository_root=root, analyst_a_path=pa, analyst_b_path=pb, output=root / "out")


@pytest.mark.parametrize(
    "bad_json", ['[{"unit_id":"pm-01","unit_id":"pm-02"}]', '[{"unit_id":NaN}]']
)
def test_builder_rejects_ambiguous_or_nonfinite_json(tmp_path: Path, bad_json: str) -> None:
    root = _sandbox(tmp_path)
    pa, pb = root / "a.json", root / "b.json"
    pa.write_text(bad_json)
    pb.write_text(json.dumps(_responses(root, "b")))
    with pytest.raises(ValueError, match=r"duplicate JSON key|non-finite"):
        build(repository_root=root, analyst_a_path=pa, analyst_b_path=pb, output=root / "out")


def test_verifier_rejects_wrong_external_lock_sha_before_git(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    lock = root / "lock.json"
    lock.write_text("{}")
    with pytest.raises(ValueError, match="analysis lock path or SHA-256 mismatch"):
        verify_locked_fixture_analysis(
            repository_root=root,
            lock_path=lock,
            expected_lock_sha256="0" * 64,
            expected_repository_commit="0" * 40,
        )


def test_verifier_rejects_alternate_authorization_path(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    pa, pb = root / "a.json", root / "b.json"
    pa.write_text(json.dumps(_responses(root, "a")))
    pb.write_text(json.dumps(_responses(root, "b")))
    output = root / "examples/v2/analyst-fixture-packet/results"
    build(repository_root=root, analyst_a_path=pa, analyst_b_path=pb, output=output)
    lock = json.loads((output / "analysis-lock.locked.json").read_text())
    alternate = root / "alternate-authorization.json"
    shutil.copy(
        root
        / "examples/v2/analyst-fixture-packet/execution-authorization.v0.2.pending-verification.json",
        alternate,
    )
    lock["authorization"] = {
        "path": "alternate-authorization.json",
        "sha256": sha256(alternate.read_bytes()).hexdigest(),
    }
    lock_path = output / "analysis-lock.locked.json"
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="authorization is not canonical"):
        verify_locked_fixture_analysis(
            repository_root=root,
            lock_path=lock_path,
            expected_lock_sha256=sha256(lock_path.read_bytes()).hexdigest(),
            expected_repository_commit="0" * 40,
        )
