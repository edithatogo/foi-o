from __future__ import annotations

from pathlib import Path

from foi_o_nz.chunks import chunk_jsonl, chunk_request_record
from foi_o_nz.dataset_metadata import (
    write_croissant_metadata,
    write_dataset_metadata,
    write_frictionless_datapackage,
    write_huggingface_dataset_card,
)
from foi_o_nz.io import iter_jsonl, write_jsonl
from foi_o_nz.ledger import build_ledger_jsonl, verify_ledger_jsonl
from foi_o_nz.openapi import build_openapi_contract, write_openapi_contract
from foi_o_nz.risk import assess_record_risk, risk_scan_jsonl


def _request_record() -> dict[str, object]:
    return {
        "schema_version": "foi-o-nz.request-profile.v0.1.0",
        "source": "fyi-archive-nz",
        "request_id": "123",
        "title": "Request for correspondence about service planning",
        "authority": "Example Ministry",
        "source_state": "waiting_response",
        "normalised_state": "Received",
    }


def test_chunk_request_record_is_content_addressed() -> None:
    chunk_a = chunk_request_record(_request_record())
    chunk_b = chunk_request_record(_request_record())

    assert chunk_a.chunk_id == chunk_b.chunk_id
    assert chunk_a.source_record_type == "request"
    assert chunk_a.token_estimate > 0
    assert len(chunk_a.text_sha256) == 64


def test_chunk_jsonl_writes_records(tmp_path: Path) -> None:
    source = tmp_path / "requests.jsonl"
    output = tmp_path / "chunks.jsonl"
    write_jsonl(source, [_request_record()])

    result = chunk_jsonl(source, output, kind="request")

    assert result["chunk_count"] == 1
    chunks = list(iter_jsonl(output))
    assert chunks[0]["source_id"] == "123"


def test_ledger_build_and_verify_detects_tamper(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    ledger = tmp_path / "events.ledger.jsonl"
    write_jsonl(
        source,
        [
            {"event_id": "foio-nz:event:1", "event_type": "RequestObserved"},
            {"event_id": "foio-nz:event:2", "event_type": "StateObserved"},
        ],
    )

    result = build_ledger_jsonl(source, ledger, record_type="event")
    assert result["entry_count"] == 2
    assert verify_ledger_jsonl(source, ledger, record_type="event")["ok"] is True

    write_jsonl(source, [{"event_id": "foio-nz:event:1", "event_type": "Tampered"}])
    tampered = verify_ledger_jsonl(source, ledger, record_type="event")
    assert tampered["ok"] is False
    assert tampered["errors"]


def test_risk_scan_flags_review_triggers(tmp_path: Path) -> None:
    record = {
        **_request_record(),
        "messages": [
            {
                "body": "Please consult because privacy is relevant. Contact test@example.org. DOB noted.",
            }
        ],
    }
    assessment = assess_record_risk(record)
    assert assessment.review_required is True
    assert assessment.risk_level in {"medium", "high"}

    source = tmp_path / "records.jsonl"
    output = tmp_path / "risks.jsonl"
    write_jsonl(source, [record])
    result = risk_scan_jsonl(source, output)
    assert result["assessment_count"] == 1
    assert list(iter_jsonl(output))[0]["review_required"] is True


def test_dataset_metadata_and_frictionless(tmp_path: Path) -> None:
    artifact = tmp_path / "requests.jsonl"
    metadata = tmp_path / "metadata.json"
    datapackage = tmp_path / "datapackage.json"
    write_jsonl(artifact, [_request_record()])

    result = write_dataset_metadata([artifact], metadata, base_dir=tmp_path)
    package_result = write_frictionless_datapackage([artifact], datapackage, base_dir=tmp_path)

    assert result["resource_count"] == 1
    assert package_result["resource_count"] == 1
    croissant = tmp_path / "croissant.json"
    card = tmp_path / "README.md"
    croissant_result = write_croissant_metadata([artifact], croissant, base_dir=tmp_path)
    card_result = write_huggingface_dataset_card([artifact], card, base_dir=tmp_path)

    assert metadata.exists()
    assert datapackage.exists()
    assert croissant.exists()
    assert card.exists()
    assert croissant_result["resource_count"] == 1
    assert card_result["resource_count"] == 1
    assert "FOI-O NZ" in card.read_text(encoding="utf-8")


def test_openapi_contract_has_guardrail_extensions(tmp_path: Path) -> None:
    output = tmp_path / "openapi.json"
    contract = build_openapi_contract()
    result = write_openapi_contract(output)

    assert contract["openapi"] == "3.1.0"
    assert result["path_count"] >= 3
    assert contract["paths"]["/agent-actions/evaluate"]["post"]["x-agent-boundary"] == "guardrail-enforcement"
