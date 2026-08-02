from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from foi_o_nz.australian_authorities import (
    AUSTRALIAN_JURISDICTIONS,
    classify_authority,
    validate_registry,
    verify_classification_result,
)

ROOT = Path(__file__).parents[1]
REGISTRY_PATH = ROOT / "examples/v2/australian-authority-registry.v1.json"


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def independent_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def repin_registry(registry: dict[str, Any]) -> None:
    body = {key: value for key, value in registry.items() if key != "self_sha256"}
    registry["self_sha256"] = independent_digest(body)


def test_registry_has_independently_verified_self_pin_and_all_profiles() -> None:
    registry = load_registry()
    claimed = registry.pop("self_sha256")
    assert claimed == independent_digest(registry)
    registry["self_sha256"] = claimed
    validate_registry(registry)
    assert {profile["jurisdiction"] for profile in registry["profiles"]} == (
        AUSTRALIAN_JURISDICTIONS
    )


@pytest.mark.parametrize(
    ("authority_id", "jurisdiction"),
    [
        ("au-cth:fixture-authority", "AU-CTH"),
        ("au-nsw:fixture-authority", "AU-NSW"),
        ("au-vic:fixture-authority", "AU-VIC"),
        ("au-qld:fixture-authority", "AU-QLD"),
        ("au-sa:fixture-authority", "AU-SA"),
        ("au-wa:fixture-authority", "AU-WA"),
        ("au-tas:fixture-authority", "AU-TAS"),
        ("au-act:fixture-authority", "AU-ACT"),
        ("au-nt:fixture-authority", "AU-NT"),
    ],
)
def test_canonical_identity_classifies_each_profile(authority_id: str, jurisdiction: str) -> None:
    evidence = {"record_id": authority_id, "authority_id": authority_id}
    result = classify_authority(evidence, load_registry(), as_of="2026-07-31")
    assert result["disposition"] == "classified"
    assert result["authority_id"] == authority_id
    assert result["jurisdiction"] == jurisdiction
    assert result["input_evidence"] == evidence
    assert result["legal_outcome_inferred"] is False
    verify_classification_result(result)


def test_alias_identity_precedes_and_retains_conflicting_tag() -> None:
    evidence = {
        "authority_name": "  WA fixture agency ",
        "tags": ["jurisdiction:act"],
        "source": {"capture_sha256": "f" * 64},
    }
    result = classify_authority(evidence, load_registry(), as_of="2026-07-31")
    assert result["disposition"] == "classified"
    assert result["authority_id"] == "au-wa:fixture-authority"
    assert result["jurisdiction"] == "AU-WA"
    assert result["basis"] == ["authority_alias"]
    assert result["conflicts"][0]["kind"] == "identity_tag_jurisdiction_conflict"
    assert result["input_evidence"] == evidence


def test_unique_tag_classifies_jurisdiction_without_inventing_authority() -> None:
    result = classify_authority(
        {"tags": ["jurisdiction:vic"]},
        load_registry(),
        as_of="2026-07-31",
    )
    assert result["disposition"] == "classified"
    assert result["jurisdiction"] == "AU-VIC"
    assert result["profile_id"] == "foi-o-au-vic"
    assert result["authority_id"] is None
    assert result["basis"] == ["platform_tag"]


def test_wa_act_tag_only_evidence_is_rejected_as_conflict() -> None:
    result = classify_authority(
        {"tags": ["jurisdiction:wa-act-ambiguous"]},
        load_registry(),
        as_of="2026-07-31",
    )
    assert result["disposition"] == "conflict"
    assert result["jurisdiction"] is None
    assert result["authority_id"] is None
    assert result["conflicts"] == [
        {
            "kind": "ambiguous_tag_only_jurisdiction",
            "jurisdictions": ["AU-ACT", "AU-WA"],
            "disposition": "identity_evidence_required",
        }
    ]


def test_unknown_evidence_remains_unresolved() -> None:
    evidence = {"authority_name": "Unregistered body", "tags": ["unknown"]}
    result = classify_authority(evidence, load_registry(), as_of="2026-07-31")
    assert result["disposition"] == "unresolved"
    assert result["candidates"] == []
    assert result["input_evidence"] == evidence


def test_explicit_out_of_scope_evidence_is_preserved() -> None:
    evidence = {
        "authority_name": "External body",
        "scope_disposition": {
            "status": "out_of_scope",
            "reason": "registry boundary",
            "source_pin": {"artifact_id": "fixture:scope", "sha256": "a" * 64},
        },
    }
    result = classify_authority(evidence, load_registry(), as_of="2026-07-31")
    assert result["disposition"] == "out_of_scope"
    assert result["input_evidence"] == evidence
    assert result["basis"] == ["explicit_scope_disposition"]


def test_tampered_registry_self_pin_is_rejected() -> None:
    registry = load_registry()
    registry["authorities"][0]["canonical_name"] = "Tampered"
    with pytest.raises(ValueError, match="self-pin mismatch"):
        validate_registry(registry)


def test_invalid_interval_is_rejected_even_with_recomputed_pin() -> None:
    registry = load_registry()
    registry["authorities"][0]["effective_interval"] = {
        "start": "2026-01-02",
        "end": "2026-01-01",
    }
    repin_registry(registry)
    with pytest.raises(ValueError, match="precedes start"):
        validate_registry(registry)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("profile_id", "foi-o-au-nsw"),
        ("regime_id", "au-nsw-gipa"),
    ],
)
def test_profile_identity_is_exact_for_its_jurisdiction(
    field: str,
    replacement: str,
) -> None:
    registry = load_registry()
    registry["profiles"][0][field] = replacement
    repin_registry(registry)
    with pytest.raises(ValueError, match="identity mismatch"):
        validate_registry(registry)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("profile_id", "foi-o-au-nsw"),
        ("regime_id", "au-nsw-gipa"),
        ("authority_id", "au-nsw:fixture-authority"),
    ],
)
def test_authority_cannot_cross_a_jurisdiction_identity_boundary(
    field: str,
    replacement: str,
) -> None:
    registry = load_registry()
    registry["authorities"][0][field] = replacement
    repin_registry(registry)
    with pytest.raises(ValueError, match="identity mismatch"):
        validate_registry(registry)


def test_authority_effective_interval_must_be_contained_by_profile() -> None:
    registry = load_registry()
    registry["authorities"][0]["effective_interval"]["start"] = "1982-11-30"
    repin_registry(registry)
    with pytest.raises(ValueError, match="outside its profile effective interval"):
        validate_registry(registry)


@pytest.mark.parametrize("history_field", ["aliases", "tag_history"])
def test_history_interval_must_be_contained_by_authority(history_field: str) -> None:
    registry = load_registry()
    registry["authorities"][0][history_field][0]["effective_interval"]["start"] = "1982-11-30"
    repin_registry(registry)
    with pytest.raises(ValueError, match="outside its authority effective interval"):
        validate_registry(registry)


def test_ambiguous_alias_is_an_explicit_identity_conflict() -> None:
    registry = load_registry()
    duplicate_alias = copy.deepcopy(registry["authorities"][0]["aliases"][0])
    duplicate_alias["effective_interval"] = copy.deepcopy(
        registry["authorities"][1]["effective_interval"]
    )
    registry["authorities"][1]["aliases"].append(duplicate_alias)
    repin_registry(registry)
    result = classify_authority(
        {"authority_name": "Commonwealth Fixture Agency"},
        registry,
        as_of="2026-07-31",
    )
    assert result["disposition"] == "conflict"
    assert result["conflicts"][0]["kind"] == "ambiguous_identity_evidence"


def test_result_digest_detects_tampering() -> None:
    result = classify_authority(
        {"authority_id": "au-nsw:fixture-authority"},
        load_registry(),
        as_of="2026-07-31",
    )
    result["jurisdiction"] = "AU-WA"
    with pytest.raises(ValueError, match="result pin mismatch"):
        verify_classification_result(result)


def test_cli_classifies_jsonl_and_preserves_evidence(tmp_path: Path) -> None:
    source = tmp_path / "evidence.jsonl"
    output = tmp_path / "classified.jsonl"
    evidence = {"record_id": "r1", "tags": ["jurisdiction:qld"]}
    source.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/classify_australian_authorities.py"),
            "--registry",
            str(REGISTRY_PATH),
            "--input",
            str(source),
            "--output",
            str(output),
            "--as-of",
            "2026-07-31",
        ],
        check=True,
        cwd=ROOT,
        env=environment,
    )
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["jurisdiction"] == "AU-QLD"
    assert result["input_evidence"] == evidence
