import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from foi_o_nz.analyst_packet_verification import (
    resolve_repo_artifact,
    verify_locked_fixture_reconciliation,
)
from scripts import build_locked_fixture_reconciliation as builder

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "examples/v2/analyst-fixture-packet/results/reconciliation-set.locked.json"
FIRST_PASS = [
    ROOT / "examples/v2/analyst-fixture-packet/results/analysis-lock.locked.json",
    ROOT / "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-a.locked.json",
    ROOT / "examples/v2/analyst-fixture-packet/results/analysis-set.analyst-b.locked.json",
]


def _write_response(tmp_path: Path, value: object) -> Path:
    path = tmp_path / "response.json"
    path.write_text(json.dumps(value, indent=2) + "\n")
    return path


def _committed_response() -> list[dict[str, Any]]:
    return [entry["record"] for entry in json.loads(OUTPUT.read_text())["entries"]]


def test_builder_is_deterministic_and_preserves_first_pass_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = [path.read_bytes() for path in FIRST_PASS]
    response = _write_response(tmp_path, _committed_response())
    monkeypatch.setattr(builder, "RESPONSE_SHA256", sha256(response.read_bytes()).hexdigest())
    builder.build(repository_root=ROOT, response_path=response, output_path=OUTPUT)
    first = OUTPUT.read_bytes()
    builder.build(repository_root=ROOT, response_path=response, output_path=OUTPUT)
    assert OUTPUT.read_bytes() == first
    assert [path.read_bytes() for path in FIRST_PASS] == before
    document = json.loads(first)
    assert document["ordered_disagreement_unit_ids"] == ["pm-06", "tl-02"]
    assert document["disagreement_count"] == len(document["entries"]) == 2
    assert document["ordered_disagreement_commitment_sha256"] == builder.canonical_sha256(
        ["pm-06", "tl-02"]
    )
    for entry in document["entries"]:
        assert entry["record_sha256"] == builder.canonical_sha256(entry["record"])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("agreement_injection", "exact ordered disagreement census"),
        ("missing", "exact ordered disagreement census"),
        ("reordered", "exact ordered disagreement census"),
        ("wrong_ref", "analysis provenance"),
        ("wrong_unit", "identity or unit"),
        ("wrong_runtime", "runtime mismatch"),
        ("wrong_label", "outside approved codebook"),
        ("empty_span", "span must be non-empty"),
        ("early_time", "timestamp ordering"),
        ("true_flag", "False was expected"),
    ],
)
def test_builder_rejects_non_governed_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str, message: str
) -> None:
    raw = _committed_response()
    if mutation == "agreement_injection":
        injected = json.loads(json.dumps(raw[0]))
        injected["record_id"] = "reconciler-fixture:pm-01"
        raw.insert(0, injected)
    elif mutation == "missing":
        raw.pop()
    elif mutation == "reordered":
        raw.reverse()
    elif mutation == "wrong_ref":
        raw[0]["analysis_refs"][0]["sha256"] = "0" * 64
    elif mutation == "wrong_unit":
        raw[0]["unit_sha256"] = "0" * 64
    elif mutation == "wrong_runtime":
        raw[0]["reconciler"]["runtime"]["session_id"] = "/root/other"
    elif mutation == "wrong_label":
        raw[0]["reconciled_candidate_label"] = "invented"
    elif mutation == "empty_span":
        raw[0]["reconciled_candidate_span"] = {
            "start": 1,
            "end": 1,
            "coordinate_system": "utf8_character_half_open",
        }
    elif mutation == "early_time":
        raw[0]["created_at"] = raw[0]["locked_at"] = "2026-07-19T03:00:00Z"
    else:
        raw[0]["human_reviewed"] = True
    path = _write_response(tmp_path, raw)
    monkeypatch.setattr(builder, "RESPONSE_SHA256", sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match=message):
        builder.build(repository_root=ROOT, response_path=path, output_path=OUTPUT)


@pytest.mark.parametrize("content", ['[{"record_id":"x","record_id":"y"}]', '[{"record_id":NaN}]'])
def test_builder_rejects_ambiguous_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str
) -> None:
    path = tmp_path / "response.json"
    path.write_text(content)
    monkeypatch.setattr(builder, "RESPONSE_SHA256", sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match=r"duplicate JSON key|non-finite"):
        builder.build(repository_root=ROOT, response_path=path, output_path=OUTPUT)


def test_builder_rejects_noncanonical_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = _write_response(tmp_path, _committed_response())
    monkeypatch.setattr(builder, "RESPONSE_SHA256", sha256(response.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="output path is not canonical"):
        builder.build(repository_root=ROOT, response_path=response, output_path=tmp_path / "x")


def test_repository_artifact_resolution_rejects_symlink_components(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "target.json"
    target.write_text("{}")
    (root / "linked.json").symlink_to(target)
    with pytest.raises(ValueError, match="contains a symlink"):
        resolve_repo_artifact(root, "linked.json")


def test_verifier_rejects_wrong_external_digest_before_git() -> None:
    with pytest.raises(ValueError, match="path or SHA-256 mismatch"):
        verify_locked_fixture_reconciliation(
            repository_root=ROOT,
            reconciliation_path=OUTPUT,
            expected_reconciliation_sha256="0" * 64,
            expected_repository_commit="0" * 40,
        )
