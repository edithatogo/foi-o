from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz import australian_immutable_manifest as manifest


def _value() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": manifest.MANIFEST_SCHEMA,
        "status": "immutable_restricted_local",
        "population": {
            "record_count": 2082,
            "completion_additions": 0,
            "completion_no_capture_slugs": 858,
        },
        "approved_inputs": manifest.PINNED_INPUTS,
        "boundaries": {"restricted_local": True, "publication_authorized": False},
    }
    payload["manifest_sha256"] = sha256(manifest._canonical_bytes(payload)).hexdigest()
    return payload


def test_validates_a_restricted_local_manifest(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(_value()))
    assert manifest.validate_manifest(path)["record_count"] == 2082


def test_rejects_manifest_with_changed_pin(tmp_path) -> None:
    value = _value()
    value["approved_inputs"] = {**manifest.PINNED_INPUTS, "source_cdx": "0" * 64}
    value["manifest_sha256"] = sha256(
        manifest._canonical_bytes({
            key: item for key, item in value.items() if key != "manifest_sha256"
        })
    ).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(value))
    with pytest.raises(ValueError, match="input pins"):
        manifest.validate_manifest(path)


def test_rejects_manifest_with_downstream_authority(tmp_path) -> None:
    value = _value()
    value["boundaries"] = {"restricted_local": True, "annotation_authorized": True}
    value["manifest_sha256"] = sha256(
        manifest._canonical_bytes({
            key: item for key, item in value.items() if key != "manifest_sha256"
        })
    ).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_bytes(manifest._canonical_bytes(value))
    with pytest.raises(ValueError, match="boundaries"):
        manifest.validate_manifest(path)


def _failure_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, Path, str]:
    failures = sorted(manifest.EXPECTED_FAILURE_SLUGS)
    records = []
    for index in range(2082):
        slug = failures[index] if index < len(failures) else f"unit-{index:04d}"
        records.append({
            "canonical_slug": slug,
            "source_url": f"https://www.righttoknow.org.au/request/{slug}.json",
            "archive_timestamp": f"20260101{index:06d}",
            "archive_digest": sha256(slug.encode()).hexdigest()[:32],
            "media_kind": "json",
        })
    selection = {
        "source_cdx_sha256": "c" * 64,
        "record_count": 2082,
        "records": records,
    }
    selection_path = tmp_path / "selection.json"
    selection_path.write_text(json.dumps(selection, sort_keys=True))
    selection_sha = sha256(selection_path.read_bytes()).hexdigest()
    monkeypatch.setitem(manifest.PINNED_INPUTS, "replay_selection", selection_sha)
    monkeypatch.setitem(manifest.PINNED_INPUTS, "source_cdx", "c" * 64)

    by_slug = {item["canonical_slug"]: item for item in records}
    ledger = {
        "schema": "foio.au-rtk-replay-failure-ledger.v1",
        "selection_sha256": selection_sha,
        "failure_count": 9,
        "failures": [
            {
                **by_slug[slug],
                "diagnostic": "Client error '404 NOT FOUND' for url 'test'",
            }
            for slug in failures
        ],
    }
    ledger_path = tmp_path / "failure-ledger.json"
    ledger_path.write_text(json.dumps(ledger, sort_keys=True))
    ledger_sha = sha256(ledger_path.read_bytes()).hexdigest()

    replay_path = tmp_path / "replay-index.jsonl"
    replay_path.write_text(
        "".join(
            json.dumps({"canonical_slug": item["canonical_slug"]}, sort_keys=True) + "\n"
            for item in records
            if item["canonical_slug"] not in manifest.EXPECTED_FAILURE_SLUGS
        )
    )
    summary = {
        "status": "candidate_non_final",
        "selection_sha256": selection_sha,
        "selected_record_count": 2082,
        "captured_record_count": 2073,
        "failure_count": 9,
        "counts": {"AU-CTH": 1574, "AU-NSW": 177, "OUT_OF_SCOPE": 112, "UNRESOLVED": 210},
        "replay_index": {"sha256": sha256(replay_path.read_bytes()).hexdigest()},
    }
    summary_path = tmp_path / "classification-summary.json"
    summary_path.write_text(json.dumps(summary, sort_keys=True))
    return selection_path, ledger_path, replay_path, summary_path, ledger_sha


def test_builds_manifest_with_explicit_404_exclusions(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selection, ledger, replay, summary, ledger_sha = _failure_inputs(tmp_path, monkeypatch)
    value = manifest.build_failure_disposition_manifest(
        replay_selection=selection,
        failure_ledger=ledger,
        replay_index=replay,
        classification_summary=summary,
        approved_failure_ledger_sha256=ledger_sha,
        authorization_confirmation=manifest.FAILURE_DISPOSITION_CONFIRMATION,
    )
    assert value["population"]["selected_position_count"] == 2082
    assert value["population"]["successful_capture_count"] == 2073
    assert value["population"]["explicit_failure_count"] == 9
    assert value["failure_disposition"]["empirical_full_text_eligible"] is False


def test_failure_manifest_requires_explicit_confirmation(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selection, ledger, replay, summary, ledger_sha = _failure_inputs(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="authorization"):
        manifest.build_failure_disposition_manifest(
            replay_selection=selection,
            failure_ledger=ledger,
            replay_index=replay,
            classification_summary=summary,
            approved_failure_ledger_sha256=ledger_sha,
            authorization_confirmation="",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("membership", "membership"),
        ("diagnostic", "HTTP 404"),
        ("provenance", "provenance"),
    ],
)
def test_failure_manifest_rejects_changed_failure_evidence(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str, message: str
) -> None:
    selection, ledger, replay, summary, _ledger_sha = _failure_inputs(tmp_path, monkeypatch)
    value = json.loads(ledger.read_text())
    if mutation == "membership":
        value["failures"][0]["canonical_slug"] = "unit-0100"
    elif mutation == "diagnostic":
        value["failures"][0]["diagnostic"] = "connection refused"
    else:
        value["failures"][0]["archive_timestamp"] = "19990101000000"
    ledger.write_text(json.dumps(value, sort_keys=True))
    with pytest.raises(ValueError, match=message):
        manifest.validate_failure_disposition_inputs(
            replay_selection=selection,
            failure_ledger=ledger,
            replay_index=replay,
            classification_summary=summary,
            approved_failure_ledger_sha256=sha256(ledger.read_bytes()).hexdigest(),
        )


def test_failure_manifest_rejects_incorrect_success_count(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selection, ledger, replay, summary, ledger_sha = _failure_inputs(tmp_path, monkeypatch)
    lines = replay.read_text().splitlines()
    replay.write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(ValueError, match="successful positions"):
        manifest.validate_failure_disposition_inputs(
            replay_selection=selection,
            failure_ledger=ledger,
            replay_index=replay,
            classification_summary=summary,
            approved_failure_ledger_sha256=ledger_sha,
        )
