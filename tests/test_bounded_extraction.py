from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from foi_o_nz.bounded_extraction import build_extraction_request, write_extraction_requests
from foi_o_nz.cli import app
from foi_o_nz.inference_providers import InferenceProviderConfig, validate_candidate_output
from foi_o_nz.io import iter_jsonl, write_jsonl

RUNNER = CliRunner()


def _source_records(path: Path) -> Path:
    write_jsonl(
        path,
        [
            {
                "request_id": "REQ-1",
                "title": "Hospital policy request",
                "body": "We have decided to release the attached policy.",
                "source_url": "https://example.test/request/1",
            }
        ],
    )
    return path


def test_build_extraction_request_is_candidate_only_with_provenance() -> None:
    request = build_extraction_request(
        {
            "request_id": "REQ-1",
            "title": "Hospital policy request",
            "body": "We have decided to release the attached policy.",
        },
        text_field="body",
        provider_config=InferenceProviderConfig(provider="deterministic"),
    )

    assert request["task_type"] == "candidate_event_extraction"
    assert request["source_id"] == "REQ-1"
    assert request["review_required"] is True
    assert request["generated_output_included"] is False
    assert request["legal_effect"] == "none"
    assert request["machine_certification_allowed"] is False
    assert request["provider_provenance"]["provider_id"] == "deterministic.feature_hash"
    assert request["provider_provenance"]["machine_certification_allowed"] is False
    assert request["input_text_sha256"]
    assert request["input_text_preview"].startswith("We have decided")
    assert request["allowed_output"]["assertion_status"] == ["observed", "inferred"]
    assert request["allowed_output"]["requires_human_review"] is True
    assert "Do not certify" in request["messages"][0]["content"]
    assert request["messages"][1]["content"] == "We have decided to release the attached policy."


def test_write_extraction_requests_outputs_safe_fixture_records(tmp_path: Path) -> None:
    source = _source_records(tmp_path / "source.jsonl")
    output = tmp_path / "requests.jsonl"

    summary = write_extraction_requests(source, output, text_field="body", max_chars=80)
    records = list(iter_jsonl(output))

    assert summary == {
        "ok": True,
        "output": str(output),
        "record_count": 1,
        "generated_output_included": False,
    }
    assert len(records) == 1
    assert records[0]["source_url"] == "https://example.test/request/1"
    assert records[0]["review_required"] is True
    assert records[0]["messages"][1]["content"] == "We have decided to release the attached policy."


def test_candidate_output_requires_human_review_for_machine_events() -> None:
    report = validate_candidate_output(
        {
            "event_id": "foio-nz:event:model-decision",
            "event_type": "DecisionCommunicated",
            "assertion_status": "inferred",
            "machine_generated": True,
            "requires_human_certification": True,
            "human_certification": {"certified": False},
            "human_review_required": False,
        }
    )

    assert report["ok"] is False
    assert any(finding["code"] == "model_output_review_required" for finding in report["findings"])
    assert report["machine_certification_allowed"] is False


def test_prepare_local_extraction_cli_writes_prompt_pack(tmp_path: Path) -> None:
    source = _source_records(tmp_path / "source.jsonl")
    output = tmp_path / "requests.jsonl"

    result = RUNNER.invoke(
        app,
        [
            "prepare-local-extraction",
            "--input",
            str(source),
            "--output",
            str(output),
            "--text-field",
            "body",
            "--provider",
            "deterministic",
            "--max-chars",
            "80",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    records = list(iter_jsonl(output))
    assert payload["record_count"] == 1
    assert payload["generated_output_included"] is False
    assert records[0]["task_type"] == "candidate_event_extraction"
    assert records[0]["machine_certification_allowed"] is False
