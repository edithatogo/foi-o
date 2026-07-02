"""Bounded local/MAX extraction request packs.

These helpers prepare prompt packs for candidate extraction experiments. They do
not call a model endpoint and they do not accept generated outputs as certified
legal decisions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from foi_o_nz.inference_providers import InferenceProviderConfig, select_embedding_provider
from foi_o_nz.io import read_json_records, write_jsonl
from foi_o_nz.max_client import draft_extraction_prompt


def build_extraction_request(
    record: dict[str, Any],
    *,
    text_field: str = "text",
    provider_config: InferenceProviderConfig | None = None,
    max_chars: int = 4000,
) -> dict[str, Any]:
    """Build a candidate-only local extraction request pack."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    text = _record_text(record, text_field=text_field)
    bounded_text = text[:max_chars]
    provider_status = select_embedding_provider(provider_config)
    source_id = _source_id(record, text)
    return {
        "task_type": "candidate_event_extraction",
        "source_id": source_id,
        "source_url": _safe_str(record.get("source_url") or record.get("url")),
        "text_field": text_field,
        "input_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "input_text_chars": len(text),
        "input_text_preview": bounded_text[:160],
        "input_truncated": len(text) > len(bounded_text),
        "messages": draft_extraction_prompt(bounded_text),
        "provider_provenance": provider_status.as_provenance(),
        "allowed_output": {
            "record_type": "candidate_event",
            "assertion_status": ["observed", "inferred"],
            "requires_human_review": True,
            "positive_human_certification": False,
            "legal_effect": "none",
        },
        "review_required": True,
        "generated_output_included": False,
        "legal_effect": "none",
        "machine_certification_allowed": False,
        "notes": [
            "Prepared prompt pack only; no model endpoint was contacted.",
            "Generated outputs must be validated and routed for human review before use.",
        ],
    }


def write_extraction_requests(
    input_path: Path,
    output_path: Path,
    *,
    text_field: str = "text",
    provider_config: InferenceProviderConfig | None = None,
    max_chars: int = 4000,
) -> dict[str, Any]:
    """Write candidate-only extraction request packs for a JSON/JSONL input."""
    records = [
        build_extraction_request(
            record,
            text_field=text_field,
            provider_config=provider_config,
            max_chars=max_chars,
        )
        for record in read_json_records(input_path)
    ]
    count = write_jsonl(output_path, records)
    return {
        "ok": True,
        "output": str(output_path),
        "record_count": count,
        "generated_output_included": False,
    }


def _record_text(record: dict[str, Any], *, text_field: str) -> str:
    value = record.get(text_field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    for fallback in ("body", "text", "response", "description", "title"):
        value = record.get(fallback)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError(f"record does not contain text in {text_field!r} or fallback text fields")


def _source_id(record: dict[str, Any], text: str) -> str:
    for field in ("request_id", "event_id", "id", "url_title"):
        value = _safe_str(record.get(field))
        if value is not None:
            return value
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:24]}"


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
