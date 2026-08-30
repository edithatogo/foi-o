from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from foi_o_nz.australian_codebook import (
    canonical_json_bytes,
    canonical_sha256,
    compose_australian_codebook,
    verify_resolved_codebook,
)

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples" / "v2"
SCHEMAS = ROOT / "schemas" / "json"


def _load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.fixture
def core() -> dict:
    return _load("australian-codebook-core.v1.json")


@pytest.fixture
def cth() -> dict:
    return _load("australian-codebook-overlay-au-cth.v1.json")


@pytest.fixture
def nsw() -> dict:
    return _load("australian-codebook-overlay-au-nsw.v1.json")


def test_examples_validate_and_compose_deterministically(core: dict, cth: dict, nsw: dict) -> None:
    core_schema = json.loads(
        (SCHEMAS / "australian-codebook-core.schema.json").read_text(encoding="utf-8")
    )
    overlay_schema = json.loads(
        (SCHEMAS / "australian-codebook-overlay.schema.json").read_text(encoding="utf-8")
    )
    resolved_schema = json.loads(
        (SCHEMAS / "australian-resolved-codebook.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(core_schema)
    Draft202012Validator.check_schema(overlay_schema)
    Draft202012Validator.check_schema(resolved_schema)
    Draft202012Validator(core_schema).validate(core)
    Draft202012Validator(overlay_schema).validate(cth)
    Draft202012Validator(overlay_schema).validate(nsw)

    first = compose_australian_codebook(core, cth)
    second = compose_australian_codebook(
        json.loads(json.dumps(core, sort_keys=False)),
        json.loads(json.dumps(cth, sort_keys=True)),
    )
    assert first == second
    assert first["span_policy"]["maximum_span_characters"] == 1000
    assert compose_australian_codebook(core, nsw)["span_policy"]["maximum_span_characters"] == 400
    Draft202012Validator(resolved_schema).validate(first)
    verify_resolved_codebook(first)


def test_hashes_use_independent_digest_calculation(core: dict, cth: dict) -> None:
    resolved = compose_australian_codebook(core, cth)
    independently_encoded = json.dumps(
        core, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert resolved["core"]["sha256"] == hashlib.sha256(independently_encoded).hexdigest()
    assert resolved["core"]["sha256"] == canonical_sha256(core)
    body = {key: value for key, value in resolved.items() if key != "self_sha256"}
    assert resolved["self_sha256"] == hashlib.sha256(canonical_json_bytes(body)).hexdigest()


@pytest.mark.parametrize("field", ["label_semantics", "abstention_semantics"])
def test_rejects_core_semantic_override(core: dict, cth: dict, field: str) -> None:
    changed = deepcopy(cth)
    changed["overrides"][field] = {}
    with pytest.raises(ValueError, match="cannot override core semantics"):
        compose_australian_codebook(core, changed)


def test_rejects_non_allowlisted_override(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["overrides"]["thresholds"] = {}
    with pytest.raises(ValueError, match="not allowlisted"):
        compose_australian_codebook(core, changed)


def test_rejects_duplicate_assertion_ids(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["assertions"].append(deepcopy(changed["assertions"][0]))
    with pytest.raises(ValueError, match="duplicate assertion IDs"):
        compose_australian_codebook(core, changed)


def test_rejects_incompatible_core_version(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["core"]["version"] = "1.1.0"
    with pytest.raises(ValueError, match="incompatible core version"):
        compose_australian_codebook(core, changed)


def test_rejects_core_with_changed_semantics_under_same_id_and_version(
    core: dict, cth: dict
) -> None:
    changed_core = deepcopy(core)
    changed_core["label_semantics"][0]["definition"] = (
        "Changed semantics concealed behind the same core identity and version."
    )
    with pytest.raises(ValueError, match="core SHA-256 does not match"):
        compose_australian_codebook(changed_core, cth)


def test_rejects_missing_core_content_pin(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    del changed["core"]["sha256"]
    with pytest.raises(ValueError, match="core SHA-256 does not match"):
        compose_australian_codebook(core, changed)


def test_rejects_unknown_as_a_current_primary_label(core: dict, cth: dict) -> None:
    changed_core = deepcopy(core)
    changed_core["label_semantics"].append({
        "id": "unknown",
        "definition": "Evidence cannot decide the assertion.",
    })
    changed = deepcopy(cth)
    changed["core"]["sha256"] = canonical_sha256(changed_core)
    with pytest.raises(ValueError, match="unknown evidence must use null-label abstention"):
        compose_australian_codebook(changed_core, changed)


def test_accepts_only_hash_pinned_legacy_unknown_mapping(core: dict, cth: dict) -> None:
    changed_core = deepcopy(core)
    changed_core["legacy_compatibility"] = {
        "source_codebook": {
            "artifact_id": "legacy-au-assertion-codebook",
            "sha256": "a" * 64,
        },
        "label_mapping": {
            "unknown": {
                "primary_label": None,
                "abstention_reason": "insufficient_evidence",
            }
        },
    }
    changed = deepcopy(cth)
    changed["core"]["sha256"] = canonical_sha256(changed_core)
    resolved = compose_australian_codebook(changed_core, changed)
    assert resolved["legacy_compatibility"] == changed_core["legacy_compatibility"]


@pytest.mark.parametrize(
    "legacy_change",
    [
        {"source_codebook": {"artifact_id": "legacy"}, "label_mapping": {}},
        {
            "source_codebook": {
                "artifact_id": "legacy",
                "sha256": "a" * 64,
            },
            "label_mapping": {
                "unknown": {
                    "primary_label": "candidate",
                    "abstention_reason": "insufficient_evidence",
                }
            },
        },
    ],
)
def test_rejects_unpinned_or_ambiguous_legacy_unknown_mapping(
    core: dict, cth: dict, legacy_change: dict
) -> None:
    changed_core = deepcopy(core)
    changed_core["legacy_compatibility"] = legacy_change
    changed = deepcopy(cth)
    changed["core"]["sha256"] = canonical_sha256(changed_core)
    with pytest.raises(ValueError, match="legacy"):
        compose_australian_codebook(changed_core, changed)


def test_calibration_abstention_is_null_with_registered_reason(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["overrides"]["calibration_examples"] = [
        {
            "label": None,
            "abstention_reason": "missing_evidence",
            "text": "The retained source has no request-linked text.",
            "rationale": "No authorized evidence is available for a primary label.",
        }
    ]
    resolved = compose_australian_codebook(core, changed)
    assert resolved["calibration_examples"][0]["label"] is None


def test_rejects_unknown_calibration_label(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["overrides"]["calibration_examples"] = [
        {
            "label": "unknown",
            "text": "Evidence is not decisive.",
            "rationale": "Legacy ambiguity must not enter a new annotation run.",
        }
    ]
    with pytest.raises(ValueError, match="primary labels or null abstentions"):
        compose_australian_codebook(core, changed)


def test_rejects_invalid_effective_interval(core: dict, cth: dict) -> None:
    changed = deepcopy(cth)
    changed["effective_interval"] = {"start": "2020-01-02", "end": "2020-01-01"}
    with pytest.raises(ValueError, match="end precedes start"):
        compose_australian_codebook(core, changed)


@pytest.mark.parametrize("pin", ["source_pack", "ontology"])
def test_rejects_missing_pin(core: dict, cth: dict, pin: str) -> None:
    changed = deepcopy(cth)
    del changed["pins"][pin]
    with pytest.raises(ValueError, match=f"{pin} pin is required"):
        compose_australian_codebook(core, changed)


@pytest.mark.parametrize("location", ["profile", "regime", "assertion"])
def test_rejects_jurisdiction_mismatch(core: dict, cth: dict, location: str) -> None:
    changed = deepcopy(cth)
    if location == "assertion":
        changed["assertions"][0]["jurisdiction"] = "AU-NSW"
    else:
        changed[location]["jurisdiction"] = "AU-NSW"
    with pytest.raises(ValueError, match="jurisdiction does not match"):
        compose_australian_codebook(core, changed)


def test_rejects_tampered_resolved_self_pin(core: dict, cth: dict) -> None:
    resolved = compose_australian_codebook(core, cth)
    resolved["assertions"][0]["statement"] = "Tampered assertion statement."
    with pytest.raises(ValueError, match="self-pin mismatch"):
        verify_resolved_codebook(resolved)
