from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from foi_o_nz import australian_replay_candidate as validator


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path, record_count: int) -> dict[str, object]:
    return {
        "path": path.name,
        "record_count": record_count,
        "byte_count": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _candidate(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    replay = tmp_path / "replay"
    raw = replay / "raw"
    records = replay / "records"
    candidate = tmp_path / "candidate"
    raw.mkdir(parents=True)
    records.mkdir()
    candidate.mkdir()
    index_rows = []
    outputs = {}
    counts = {"AU-CTH": 1, "AU-NSW": 1, "OUT_OF_SCOPE": 0, "UNRESOLVED": 0}
    for jurisdiction, slug, media in (
        ("AU-CTH", "cth", "json"),
        ("AU-NSW", "nsw", "html"),
    ):
        raw_path = raw / f"{slug}.{media}"
        raw_path.write_bytes(slug.encode())
        parsed_path = records / f"{slug}.json"
        source_url = f"https://www.righttoknow.org.au/request/{slug}"
        archive_url = f"https://web.archive.org/web/20200101000000id_/{source_url}"
        base = {
            "canonical_slug": slug,
            "media_kind": media,
            "source_url": source_url,
            "archive_url": archive_url,
            "archive_timestamp": "20200101000000",
            "archive_digest": slug.upper(),
            "raw_sha256": _sha256(raw_path),
            "status": "captured",
            "parser_version": 3,
            "jurisdiction": jurisdiction,
        }
        parsed_path.write_text(json.dumps(base) + "\n")
        index_rows.append(
            {
                **{field: base[field] for field in validator.PROVENANCE_FIELDS},
                "raw_filename": raw_path.name,
                "raw_byte_count": raw_path.stat().st_size,
                "record_filename": parsed_path.name,
                "record_byte_count": parsed_path.stat().st_size,
                "record_sha256": _sha256(parsed_path),
            }
        )
        output = candidate / f"{jurisdiction}.jsonl"
        output.write_text(json.dumps(base) + "\n")
        outputs[jurisdiction] = _artifact(output, 1)
    for jurisdiction in ("OUT_OF_SCOPE", "UNRESOLVED"):
        output = candidate / f"{jurisdiction}.jsonl"
        output.write_text("")
        outputs[jurisdiction] = _artifact(output, 0)
    index_path = candidate / "index.jsonl"
    index_path.write_text("".join(json.dumps(row) + "\n" for row in index_rows))
    summary = {
        "schema": "fyi-archive.au-rtk-jurisdiction-classification-candidate.v1",
        "status": "candidate_non_final",
        "source_cdx_sha256": "954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd",
        "selection_sha256": "a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51",
        "captured_record_count": 2,
        "counts": counts,
        "replay_index": _artifact(index_path, 2),
        "jurisdiction_outputs": outputs,
        "publication": False,
        "redistribution": False,
        "manifest_finalization_authorized": False,
    }
    schema = json.loads(validator.SCHEMA.read_text())
    schema["properties"]["captured_record_count"] = {"const": 2}
    monkeypatch.setattr(validator, "SCHEMA", tmp_path / "schema.json")
    validator.SCHEMA.write_text(json.dumps(schema))
    summary_path = candidate / "summary.json"
    summary_path.write_text(json.dumps(summary))
    return summary_path, replay


def test_independent_validator_checks_exact_source_partition(tmp_path, monkeypatch) -> None:
    summary, replay = _candidate(tmp_path, monkeypatch)
    result = validator.validate_replay_candidate(summary, replay_root=replay)
    assert result["ok"] is True
    assert result["counts"] == {
        "AU-CTH": 1,
        "AU-NSW": 1,
        "OUT_OF_SCOPE": 0,
        "UNRESOLVED": 0,
    }
    assert result["manifest_finalization_authorized"] is False


def test_independent_validator_rejects_changed_raw_source(tmp_path, monkeypatch) -> None:
    summary, replay = _candidate(tmp_path, monkeypatch)
    (replay / "raw/cth.json").write_text("xyz")
    with pytest.raises(ValueError, match="raw replay cth SHA-256 mismatch"):
        validator.validate_replay_candidate(summary, replay_root=replay)


def test_independent_validator_rejects_live_origin_archive_url(tmp_path, monkeypatch) -> None:
    summary, replay = _candidate(tmp_path, monkeypatch)
    payload = json.loads(summary.read_text())
    output = summary.parent / payload["jurisdiction_outputs"]["AU-CTH"]["path"]
    row = json.loads(output.read_text())
    row["archive_url"] = row["source_url"]
    output.write_text(json.dumps(row) + "\n")
    payload["jurisdiction_outputs"]["AU-CTH"] = _artifact(output, 1)
    summary.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="archive URL escaped Internet Archive"):
        validator.validate_replay_candidate(summary, replay_root=replay)
